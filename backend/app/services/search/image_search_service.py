import gc
import os
import sys
import traceback

import faiss
import numpy as np
import torch

from PIL import Image
from sentence_transformers import SentenceTransformer

from app.services.analytics.search_tracking_service import SearchTrackingService
from app.models.enums import SearchType
from app.database.session import SessionLocal
from app.models.product import Product


class ImageSearchService:

    def __init__(self):

        print("[ImageSearchService] STEP 0 - Initializing ImageSearchService...", flush=True)
        print(f"[ImageSearchService] Python version : {sys.version}", flush=True)
        print(f"[ImageSearchService] Working dir    : {os.getcwd()}", flush=True)

        # ------------------------------------------------------------------ #
        # STEP 1 — SentenceTransformer / CLIP model                           #
        # Most likely failure point on Railway:                                #
        #   - HuggingFace download timeout (no cached model)                  #
        #   - OOM during model weight allocation                               #
        #   - TRANSFORMERS_OFFLINE=1 set but no cached model present          #
        # ------------------------------------------------------------------ #
        print("[ImageSearchService] STEP 1a - Attempting to load SentenceTransformer('clip-ViT-B-32')...", flush=True)
        print(
            f"[ImageSearchService] STEP 1a - HF cache dir: "
            f"{os.environ.get('SENTENCE_TRANSFORMERS_HOME', os.environ.get('HF_HOME', '<default>'))}",
            flush=True
        )

        try:
            self.model = SentenceTransformer("clip-ViT-B-32")
        except Exception:
            print(
                "[ImageSearchService] STEP 1a - FAILED loading SentenceTransformer:\n"
                + traceback.format_exc(),
                flush=True,
            )
            raise RuntimeError(
                "ImageSearchService: SentenceTransformer('clip-ViT-B-32') failed to load. "
                "Check Railway logs for full traceback. "
                "Likely cause: HuggingFace download failed or OOM during weight allocation."
            )

        print("[ImageSearchService] STEP 1b - SentenceTransformer loaded. Switching to eval mode...", flush=True)

        try:
            # Inference-only: disable gradient tracking for the entire model.
            self.model.eval()
            for param in self.model.parameters():
                param.requires_grad_(False)
        except Exception:
            print(
                "[ImageSearchService] STEP 1b - FAILED setting eval/no_grad:\n"
                + traceback.format_exc(),
                flush=True,
            )
            raise

        print("[ImageSearchService] STEP 1 - Model loaded and configured (clip-ViT-B-32).", flush=True)

        # ------------------------------------------------------------------ #
        # STEP 2 — FAISS index                                                 #
        # Failure modes:                                                        #
        #   - File not deployed to Railway (not committed to git)              #
        #   - Wrong working directory (CWD not /backend)                       #
        #   - Corrupted .faiss file                                            #
        # ------------------------------------------------------------------ #
        faiss_path = "faiss_indexes/image_index.faiss"
        print(f"[ImageSearchService] STEP 2a - Loading FAISS index from: {os.path.abspath(faiss_path)}", flush=True)
        print(f"[ImageSearchService] STEP 2a - File exists: {os.path.isfile(faiss_path)}", flush=True)

        try:
            self.index = faiss.read_index(faiss_path)
        except Exception:
            print(
                f"[ImageSearchService] STEP 2a - FAILED loading FAISS index '{faiss_path}':\n"
                + traceback.format_exc(),
                flush=True,
            )
            raise RuntimeError(
                f"ImageSearchService: faiss.read_index('{faiss_path}') failed. "
                f"Absolute path tried: {os.path.abspath(faiss_path)}. "
                f"File exists on disk: {os.path.isfile(faiss_path)}. "
                f"Check that faiss_indexes/image_index.faiss is committed and deployed."
            )

        print(
            f"[ImageSearchService] STEP 2 - FAISS index loaded. "
            f"Total vectors: {self.index.ntotal}, Dimension: {self.index.d}",
            flush=True,
        )

        # ------------------------------------------------------------------ #
        # STEP 3 — Product ID mapping (.npy)                                   #
        # Failure modes:                                                        #
        #   - File not deployed to Railway                                     #
        #   - Wrong working directory                                          #
        #   - File saved with allow_pickle=True but loaded with False          #
        # ------------------------------------------------------------------ #
        npy_path = "embeddings/image/image_product_ids.npy"
        print(f"[ImageSearchService] STEP 3a - Loading product IDs from: {os.path.abspath(npy_path)}", flush=True)
        print(f"[ImageSearchService] STEP 3a - File exists: {os.path.isfile(npy_path)}", flush=True)

        try:
            self.product_ids = np.load(npy_path, allow_pickle=False)
        except Exception:
            print(
                f"[ImageSearchService] STEP 3a - FAILED loading product IDs '{npy_path}':\n"
                + traceback.format_exc(),
                flush=True,
            )
            raise RuntimeError(
                f"ImageSearchService: np.load('{npy_path}') failed. "
                f"Absolute path tried: {os.path.abspath(npy_path)}. "
                f"File exists on disk: {os.path.isfile(npy_path)}."
            )

        print(
            f"[ImageSearchService] STEP 3 - Product IDs loaded. Count: {len(self.product_ids)}",
            flush=True,
        )

        # ------------------------------------------------------------------ #
        # STEP 4 — Alignment check                                             #
        # ------------------------------------------------------------------ #
        if self.index.ntotal != len(self.product_ids):
            msg = (
                f"[ImageSearchService] STEP 4 - ALIGNMENT MISMATCH: "
                f"FAISS has {self.index.ntotal} vectors but "
                f"product_ids has {len(self.product_ids)} entries. "
                f"Re-run the indexing script to rebuild both files together."
            )
            print(msg, flush=True)
            raise ValueError(msg)

        print("[ImageSearchService] STEP 4 - ImageSearchService ready. All checks passed.", flush=True)

    # ---------------------------------------------------------------------- #
    # search()                                                                 #
    # ---------------------------------------------------------------------- #
    def search(self, image_path, top_k=5):

        print(f"[ImageSearchService] Image received: {image_path}", flush=True)

        # ------------------------------------------------------------------ #
        # 1. Load image — context manager releases PIL bitmap immediately      #
        #    after encoding, before any DB work.                               #
        # ------------------------------------------------------------------ #
        try:
            with Image.open(image_path).convert("RGB") as image:
                # ---------------------------------------------------------- #
                # 2. Encode — torch.no_grad() prevents gradient graph         #
                #    accumulation (memory leak) across requests.               #
                # ---------------------------------------------------------- #
                with torch.no_grad():
                    query_embedding = self.model.encode(
                        image,
                        convert_to_numpy=True,
                        normalize_embeddings=True,
                    ).astype("float32")
        except Exception:
            print(
                f"[ImageSearchService] FAILED during image encode '{image_path}':\n"
                + traceback.format_exc(),
                flush=True,
            )
            raise

        # Guarantee shape is (1, dim) for FAISS
        if query_embedding.ndim == 1:
            query_embedding = np.expand_dims(query_embedding, axis=0)

        print(
            f"[ImageSearchService] Embedding shape: {query_embedding.shape} "
            f"(FAISS index dim: {self.index.d})",
            flush=True,
        )

        if query_embedding.shape[1] != self.index.d:
            raise ValueError(
                f"[ImageSearchService] Embedding dim {query_embedding.shape[1]} "
                f"does not match FAISS index dim {self.index.d}. "
                f"Ensure the same clip-ViT-B-32 model was used during indexing."
            )

        # ------------------------------------------------------------------ #
        # 3. FAISS search                                                      #
        # ------------------------------------------------------------------ #
        distances, indices = self.index.search(query_embedding, top_k)

        print(
            f"[ImageSearchService] FAISS search completed. "
            f"Raw indices: {indices[0].tolist()}",
            flush=True,
        )

        del query_embedding

        # ------------------------------------------------------------------ #
        # 4. Resolve product IDs → DB                                          #
        # ------------------------------------------------------------------ #
        db = SessionLocal()

        try:
            results = []

            for idx, distance in zip(indices[0], distances[0]):

                if idx < 0 or idx >= len(self.product_ids):
                    continue

                product_id = int(self.product_ids[idx])

                product = (
                    db.query(Product)
                    .filter(Product.id == product_id)
                    .first()
                )

                if product:
                    results.append(
                        {
                            "product": product,
                            "score": 1 / (1 + float(distance)),
                        }
                    )

            print(f"[ImageSearchService] Results returned: {len(results)}", flush=True)

            # -------------------------------------------------------------- #
            # 5. Analytics                                                      #
            # -------------------------------------------------------------- #
            tracker = SearchTrackingService()
            tracker.log_search(
                query=image_path,
                search_type=SearchType.IMAGE,
                results_count=len(results),
            )

            return results

        finally:
            db.close()