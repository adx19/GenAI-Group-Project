from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.search import router as search_router
from app.api.analytics import router as analytics_router
from app.api.products import router as product_router




@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load services to warm up models on startup
    from app.api.search import get_text_service, get_image_service
    try:
        get_text_service()
    except Exception:
        import traceback
        traceback.print_exc()
    try:
        get_image_service()
    except Exception:
        import traceback
        traceback.print_exc()
    yield


app = FastAPI(
    title="GenAI Product Discovery System",
    lifespan=lifespan,
)

# --- CORS middleware (original config — NOT modified) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gen-ai-group-project-pi.vercel.app"
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
        "message": "Product Discovery API Running",
    }
