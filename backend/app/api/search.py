import datetime
import os
from pathlib import Path
import shutil
import traceback
import uuid

from fastapi import APIRouter
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
from pydantic import BaseModel

from app.database.session import SessionLocal
from app.models.product_attribute import ProductAttribute

# ---------------------------------------------------------------------------
# DIAGNOSTIC: module-scope import marker
# This block executes once per Python process that imports this module.
# If it appears twice with different PIDs → multi-worker.
# If it appears twice with the same PID → module is being reimported
# (should never happen in a healthy app — would reset all singletons).
# ---------------------------------------------------------------------------
_SEARCH_MODULE_IMPORT_PID = os.getpid()
_SEARCH_MODULE_IMPORT_TIME = datetime.datetime.utcnow().isoformat()
print(
    f"\n[search.py MODULE IMPORT]"
    f" pid={_SEARCH_MODULE_IMPORT_PID}"
    f" time={_SEARCH_MODULE_IMPORT_TIME}"
    f" WEB_CONCURRENCY={os.environ.get('WEB_CONCURRENCY', 'not set')}",
    flush=True,
)


router = APIRouter(
    prefix="/search",
    tags=["Search"]
)

text_service = None
image_service = None
multimodal_service = None

print(
    f"[search.py] pid={os.getpid()}"
    f" singletons initialised: text_service=None image_service=None multimodal_service=None",
    flush=True,
)


def get_text_service():
    global text_service

    pid = os.getpid()
    if text_service is None:
        print(f"[get_text_service] pid={pid} CREATING TextSearchService...", flush=True)
        from app.services.search.text_search_service import TextSearchService
        text_service = TextSearchService()
        print(f"[get_text_service] pid={pid} CREATED id={id(text_service)}", flush=True)
    else:
        print(f"[get_text_service] pid={pid} REUSING id={id(text_service)}", flush=True)

    return text_service


def get_image_service():
    global image_service

    pid = os.getpid()
    if image_service is None:
        print(f"[get_image_service] pid={pid} CREATING ImageSearchService...", flush=True)
        from app.services.search.image_search_service import ImageSearchService
        try:
            image_service = ImageSearchService()
            print(f"[get_image_service] pid={pid} CREATED id={id(image_service)}", flush=True)
        except Exception:
            print(
                f"[get_image_service] pid={pid} FAILED:\n" + traceback.format_exc(),
                flush=True,
            )
            raise
    else:
        print(f"[get_image_service] pid={pid} REUSING id={id(image_service)}", flush=True)

    return image_service


def get_multimodal_service():
    global multimodal_service

    pid = os.getpid()
    if multimodal_service is None:
        print(f"[get_multimodal_service] pid={pid} CREATING MultimodalSearchService...", flush=True)
        from app.services.search.multimodal_search_service import MultimodalSearchService
        multimodal_service = MultimodalSearchService()
        print(f"[get_multimodal_service] pid={pid} CREATED id={id(multimodal_service)}", flush=True)
    else:
        print(f"[get_multimodal_service] pid={pid} REUSING id={id(multimodal_service)}", flush=True)

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
    # Use a uuid-based name so a None/missing filename never crashes
    # before the finally-block can clean up.
    suffix = Path(image.filename).suffix if image.filename else ".jpg"
    file_path = TEMP_UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"

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

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    finally:
        if file_path.exists():
            file_path.unlink()


@router.post("/multimodal")
async def multimodal_search(
    image: UploadFile = File(...),
    query: str = Form(...)
):
    suffix = Path(image.filename).suffix if image.filename else ".jpg"
    file_path = TEMP_UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"

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

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    finally:
        if file_path.exists():
            file_path.unlink()