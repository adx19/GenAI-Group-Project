from pathlib import Path
import shutil

from fastapi import APIRouter
from fastapi import File
from fastapi import Form
from fastapi import UploadFile
from pydantic import BaseModel

from app.database.session import SessionLocal
from app.models.product_attribute import ProductAttribute


router = APIRouter(
    prefix="/search",
    tags=["Search"]
)

text_service = None
image_service = None
multimodal_service = None


def get_text_service():
    global text_service

    if text_service is None:
        print("Loading Text Search Service...")

        from app.services.search.text_search_service import TextSearchService

        text_service = TextSearchService()

    return text_service


def get_image_service():
    global image_service

    if image_service is None:
        print("[image_service] Loading Image Search Service (first request)...")

        from app.services.search.image_search_service import ImageSearchService

        image_service = ImageSearchService()

        print("[image_service] Image Search Service ready.")

    return image_service


def get_multimodal_service():
    global multimodal_service

    if multimodal_service is None:
        print("Loading Multimodal Search Service...")

        from app.services.search.multimodal_search_service import MultimodalSearchService

        multimodal_service = MultimodalSearchService()

    return multimodal_service

TEMP_UPLOAD_DIR = Path("temp_uploads")
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)


def build_product_response(product, score):

    db = SessionLocal()

    try:

        attributes = (
            db.query(ProductAttribute)
            .filter(
                ProductAttribute.product_id == product.id
            )
            .first()
        )

        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "image_url": product.image_url,
            "category": product.category,
            "score": score,
            "attributes": {
                "color": (
                    attributes.color
                    if attributes
                    else None
                ),
                "material": (
                    attributes.material
                    if attributes
                    else None
                ),
                "style": (
                    attributes.style
                    if attributes
                    else None
                ),
                "shape": (
                    attributes.shape
                    if attributes
                    else None
                )
            }
        }

    finally:
        db.close()


class TextSearchRequest(BaseModel):
    query: str
    top_k: int = 10


@router.post("/text")
def text_search(request: TextSearchRequest):

    results = get_text_service().search(
        query=request.query,
        top_k=request.top_k
    )

    return {
        "results": [
            build_product_response(
                r["product"],
                r["score"]
            )
            for r in results
        ]
    }


@router.post("/image")
async def image_search(
    image: UploadFile = File(...)
):

    file_path = TEMP_UPLOAD_DIR / image.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(
            image.file,
            buffer
        )

    try:

        results = get_image_service().search(
            image_path=str(file_path),
            top_k=10
        )

        return {
            "results": [
                build_product_response(
                    r["product"],
                    r["score"]
                )
                for r in results
            ]
        }

    finally:

        if file_path.exists():
            file_path.unlink()


@router.post("/multimodal")
async def multimodal_search(
    image: UploadFile = File(...),
    query: str = Form(...)
):

    file_path = TEMP_UPLOAD_DIR / image.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(
            image.file,
            buffer
        )

    try:

        results = get_multimodal_service().search(
            text_query=query,
            image_path=str(file_path),
            top_k=10
        )

        return {
            "results": [
                build_product_response(
                    r["product"],
                    r["score"]
                )
                for r in results
            ]
        }

    finally:

        if file_path.exists():
            file_path.unlink()