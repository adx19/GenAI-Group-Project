from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.search import router as search_router
from app.api.analytics import router as analytics_router
from app.api.products import router as product_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Pre-load all search services at startup, sequentially.

    WHY: Lazy loading means the first /multimodal request triggers both
    TextSearchService AND ImageSearchService to load simultaneously
    (TextSearchService on the call stack, ImageSearchService already resident).
    That peak RAM spike is what OOM-kills the Railway process.

    Loading them sequentially at startup means each model's download/init
    peak is isolated, and by request-time both are already resident and
    their combined steady-state RAM is well within the limit.
    """
    from app.api.search import get_text_service, get_image_service

    print("[startup] Pre-loading TextSearchService...", flush=True)
    try:
        get_text_service()
        print("[startup] TextSearchService ready.", flush=True)
    except Exception as e:
        print(f"[startup] WARNING: TextSearchService failed to load: {e}", flush=True)

    print("[startup] Pre-loading ImageSearchService...", flush=True)
    try:
        get_image_service()
        print("[startup] ImageSearchService ready.", flush=True)
    except Exception as e:
        print(f"[startup] WARNING: ImageSearchService failed to load: {e}", flush=True)

    print("[startup] All services pre-loaded. Accepting requests.", flush=True)
    yield
    # Shutdown — nothing to clean up explicitly


app = FastAPI(
    title="GenAI Product Discovery System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gen-ai-group-project-git-main-adx19s-projects.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(analytics_router)
app.include_router(product_router)


@app.get("/")
def root():

    return {
        "message": "Product Discovery API Running"
    }