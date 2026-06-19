import os

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
        # ------------------------------------------------------------------ #
        # STEP 1 — Load EfficientNet-B0                                      #
        # ------------------------------------------------------------------ #
        try:
            weights = models.EfficientNet_B0_Weights.DEFAULT
            self.model = models.efficientnet_b0(weights=weights)
            # Remove Linear(1280 → 1000) classifier → model now outputs (batch, 1280)
            self.model.classifier = torch.nn.Identity()
            self.model.eval()
            # Official ImageNet preprocessing: Resize(256)→CenterCrop(224)→Normalize
            # Must be identical to the pipeline used in generate_image_embeddings.py
            self.preprocess = weights.transforms()
        except Exception as e:
            raise RuntimeError(
                "ImageSearchService: EfficientNet-B0 failed to load. "
                "Ensure torchvision is installed and internet access is available "
                "for the first weights download."
            ) from e

        # ------------------------------------------------------------------ #
        # STEP 2 — FAISS index                                               #
        # ------------------------------------------------------------------ #
        faiss_path = "faiss_indexes/image_index.faiss"
        try:
            self.index = faiss.read_index(faiss_path)
        except Exception as e:
            raise RuntimeError(
                f"ImageSearchService: faiss.read_index('{faiss_path}') failed. "
                f"File exists: {os.path.isfile(faiss_path)}. "
                f"Ensure faiss_indexes/image_index.faiss is committed and deployed."
            ) from e

        # ------------------------------------------------------------------ #
        # STEP 3 — Product ID mapping                                        #
        # ------------------------------------------------------------------ #
        npy_path = "embeddings/image/image_product_ids.npy"
        try:
            self.product_ids = np.load(npy_path, allow_pickle=False)
        except Exception as e:
            raise RuntimeError(
                f"ImageSearchService: np.load('{npy_path}') failed. "
                f"File exists: {os.path.isfile(npy_path)}."
            ) from e

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
            raise ValueError(msg)

        if self.index.ntotal != len(self.product_ids):
            msg = (
                f"[ImageSearchService] STEP 4 COUNT MISMATCH: "
                f"FAISS has {self.index.ntotal} vectors but "
                f"product_ids has {len(self.product_ids)} entries."
            )
            raise ValueError(msg)

    # ---------------------------------------------------------------------- #
    # search()                                                               #
    # ---------------------------------------------------------------------- #
    def search(self, image_path: str, top_k: int = 5):
        # 1. Load image and encode with EfficientNet-B0
        with Image.open(image_path).convert("RGB") as img:
            # preprocess: Resize(256) → CenterCrop(224) → ToTensor → Normalize
            tensor = self.preprocess(img).unsqueeze(0)   # (1, 3, 224, 224)

        with torch.no_grad():
            embedding = self.model(tensor).cpu().numpy().flatten()  # (1280,)

        query_embedding = embedding.reshape(1, -1).astype("float32")

        if query_embedding.shape[1] != self.index.d:
            raise ValueError(
                f"[ImageSearchService] Runtime dim mismatch: "
                f"query={query_embedding.shape[1]}, index={self.index.d}. "
                f"Regenerate embeddings and FAISS index."
            )

        # 2. FAISS search
        distances, indices = self.index.search(query_embedding, top_k)
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