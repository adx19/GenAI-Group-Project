from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.search import router as search_router
from app.api.analytics import router as analytics_router
from app.api.products import router as product_router

app = FastAPI(
    title="GenAI Product Discovery System"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
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