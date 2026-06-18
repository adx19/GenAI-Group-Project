import datetime
import os
import sys
import traceback

import faiss
import numpy as np
import torch
from PIL import Image
from torchvision import models

from app.services.analytics.search_tracking_service import SearchTrackingService
from app.models.enums import SearchType
from app.database.session import SessionLocal
from app.models.product import Product

# ---------------------------------------------------------------------------
# EfficientNet-B0 configuration
#
# WHY EfficientNet-B0 (replaced CLIP ViT-B/32):
#   CLIP ViT-B/32: 151 M params, float32 → ~576 MB RSS
#   EfficientNet-B0: 5.3 M params, float32 → ~21 MB RSS
#   Saving: ~555 MB — brings Railway RSS from ~838 MB to ~283 MB
#
# The classifier head is removed so the model outputs (batch, 1280) embeddings.
# The preprocessing pipeline uses weights.transforms() — the same pipeline
# that generate_image_embeddings.py used to build the FAISS index.
# DO NOT change the model without regenerating embeddings and the FAISS index.
# ---------------------------------------------------------------------------
_MODEL_NAME = "efficientnet_b0"
_EMBED_DIM = 1280   # EfficientNet-B0 avgpool output, after stripping classifier


class ImageSearchService:

    def __init__(self):
        pid = os.getpid()
        ts = datetime.datetime.utcnow().isoformat()
        print(
            f"[ImageSearchService] CREATED pid={pid} id={id(self)} time={ts}",
            flush=True,
        )
        print(f"[ImageSearchService] Torch version : {torch.__version__}", flush=True)
        print(f"[ImageSearchService] CUDA available: {torch.cuda.is_available()}", flush=True)
        print(f"[ImageSearchService] Python        : {sys.version}", flush=True)
        print(f"[ImageSearchService] Working dir   : {os.getcwd()}", flush=True)

        # ------------------------------------------------------------------ #
        # STEP 1 — Load EfficientNet-B0                                      #
        # ------------------------------------------------------------------ #
        print(
            f"[ImageSearchService] STEP 1 - Loading EfficientNet-B0 (ImageNet weights)...",
            flush=True,
        )
        try:
            weights = models.EfficientNet_B0_Weights.DEFAULT
            self.model = models.efficientnet_b0(weights=weights)
            # Remove Linear(1280 → 1000) classifier → model now outputs (batch, 1280)
            self.model.classifier = torch.nn.Identity()
            self.model.eval()
            # Official ImageNet preprocessing: Resize(256)→CenterCrop(224)→Normalize
            # Must be identical to the pipeline used in generate_image_embeddings.py
            self.preprocess = weights.transforms()
            print(
                f"[ImageSearchService] STEP 1 COMPLETE - EfficientNet-B0 ready. "
                f"embed_dim={_EMBED_DIM}",
                flush=True,
            )
        except Exception:
            print(
                "[ImageSearchService] STEP 1 FAILED loading EfficientNet-B0:\n"
                + traceback.format_exc(),
                flush=True,
            )
            raise RuntimeError(
                "ImageSearchService: EfficientNet-B0 failed to load. "
                "Ensure torchvision is installed and internet access is available "
                "for the first weights download."
            )

        # ------------------------------------------------------------------ #
        # STEP 2 — FAISS index                                               #
        # ------------------------------------------------------------------ #
        faiss_path = "faiss_indexes/image_index.faiss"
        print(
            f"[ImageSearchService] STEP 2 - Loading FAISS index: "
            f"{os.path.abspath(faiss_path)} (exists={os.path.isfile(faiss_path)})",
            flush=True,
        )
        try:
            self.index = faiss.read_index(faiss_path)
        except Exception:
            print(
                "[ImageSearchService] STEP 2 FAILED loading FAISS index:\n"
                + traceback.format_exc(),
                flush=True,
            )
            raise RuntimeError(
                f"ImageSearchService: faiss.read_index('{faiss_path}') failed. "
                f"File exists: {os.path.isfile(faiss_path)}. "
                f"Ensure faiss_indexes/image_index.faiss is committed and deployed."
            )
        print(
            f"[ImageSearchService] STEP 2 - FAISS index loaded. "
            f"ntotal={self.index.ntotal}, dim={self.index.d}",
            flush=True,
        )

        # ------------------------------------------------------------------ #
        # STEP 3 — Product ID mapping                                        #
        # ------------------------------------------------------------------ #
        npy_path = "embeddings/image/image_product_ids.npy"
        print(
            f"[ImageSearchService] STEP 3 - Loading product IDs: "
            f"{os.path.abspath(npy_path)} (exists={os.path.isfile(npy_path)})",
            flush=True,
        )
        try:
            self.product_ids = np.load(npy_path, allow_pickle=False)
        except Exception:
            print(
                "[ImageSearchService] STEP 3 FAILED loading product IDs:\n"
                + traceback.format_exc(),
                flush=True,
            )
            raise RuntimeError(
                f"ImageSearchService: np.load('{npy_path}') failed. "
                f"File exists: {os.path.isfile(npy_path)}."
            )
        print(
            f"[ImageSearchService] STEP 3 - Product IDs loaded. "
            f"count={len(self.product_ids)}",
            flush=True,
        )

        # ------------------------------------------------------------------ #
        # STEP 4 — Dimension alignment check                                 #
        # ------------------------------------------------------------------ #
        if self.index.d != _EMBED_DIM:
            msg = (
                f"[ImageSearchService] STEP 4 DIM MISMATCH: "
                f"FAISS index dim={self.index.d} but model output dim={_EMBED_DIM}. "
                f"Regenerate embeddings with scripts/generate_image_embeddings.py "
                f"then rebuild the index with scripts/build_image_faiss.py."
            )
            print(msg, flush=True)
            raise ValueError(msg)

        if self.index.ntotal != len(self.product_ids):
            msg = (
                f"[ImageSearchService] STEP 4 COUNT MISMATCH: "
                f"FAISS has {self.index.ntotal} vectors but "
                f"product_ids has {len(self.product_ids)} entries."
            )
            print(msg, flush=True)
            raise ValueError(msg)

        print(
            f"[ImageSearchService] STEP 4 - Alignment OK. "
            f"Serving {self.index.ntotal} products at dim={self.index.d}.",
            flush=True,
        )

    # ---------------------------------------------------------------------- #
    # search()                                                               #
    # ---------------------------------------------------------------------- #
    def search(self, image_path: str, top_k: int = 5):
        print(f"[ImageSearchService] Image received: {image_path}", flush=True)

        # 1. Load image and encode with EfficientNet-B0
        try:
            with Image.open(image_path).convert("RGB") as img:
                # preprocess: Resize(256) → CenterCrop(224) → ToTensor → Normalize
                tensor = self.preprocess(img).unsqueeze(0)   # (1, 3, 224, 224)

            with torch.no_grad():
                embedding = self.model(tensor).cpu().numpy().flatten()  # (1280,)

        except Exception:
            print(
                "[ImageSearchService] FAILED during image encode:\n"
                + traceback.format_exc(),
                flush=True,
            )
            raise

        query_embedding = embedding.reshape(1, -1).astype("float32")

        print(
            f"[ImageSearchService] Embedding shape: {query_embedding.shape} "
            f"(FAISS dim: {self.index.d})",
            flush=True,
        )

        if query_embedding.shape[1] != self.index.d:
            raise ValueError(
                f"[ImageSearchService] Runtime dim mismatch: "
                f"query={query_embedding.shape[1]}, index={self.index.d}. "
                f"Regenerate embeddings and FAISS index."
            )

        # 2. FAISS search
        distances, indices = self.index.search(query_embedding, top_k)
        print(
            f"[ImageSearchService] FAISS search done. "
            f"indices={indices[0].tolist()}",
            flush=True,
        )
        del query_embedding

        # 3. Resolve product IDs → DB
        db = SessionLocal()
        try:
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < 0 or idx >= len(self.product_ids):
                    continue
                product_id = int(self.product_ids[idx])
                product = db.query(Product).filter(Product.id == product_id).first()
                if product:
                    results.append({
                        "product": product,
                        "score": 1 / (1 + float(distance)),
                    })

            print(f"[ImageSearchService] Results returned: {len(results)}", flush=True)

            # 4. Analytics
            tracker = SearchTrackingService()
            tracker.log_search(
                query=image_path,
                search_type=SearchType.IMAGE,
                results_count=len(results),
            )
            return results

        finally:
            db.close()