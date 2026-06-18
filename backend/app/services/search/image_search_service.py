import gc
import os
import sys
import traceback

import faiss
import numpy as np
import torch

from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from app.services.analytics.search_tracking_service import SearchTrackingService
from app.models.enums import SearchType
from app.database.session import SessionLocal
from app.models.product import Product

# ---------------------------------------------------------------------------
# Model name — must match what was used in generate_image_embeddings.py
# FAISS index was built from CLIPModel("openai/clip-vit-base-patch32")
# embeddings.  Do NOT change this without rebuilding the FAISS index.
# ---------------------------------------------------------------------------
_CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"


class ImageSearchService:

    def __init__(self):

        print("[ImageSearchService] STEP 0 - Initializing...", flush=True)
        print(f"[ImageSearchService] Python     : {sys.version}", flush=True)
        print(f"[ImageSearchService] Working dir: {os.getcwd()}", flush=True)
        print(f"[ImageSearchService] Torch      : {torch.__version__}", flush=True)

        # ------------------------------------------------------------------ #
        # STEP 1 — Load CLIPProcessor (lightweight — just tokenizer/config)   #
        # ------------------------------------------------------------------ #
        print(
            f"[ImageSearchService] STEP 1a - Loading CLIPProcessor "
            f"from '{_CLIP_MODEL_NAME}'...",
            flush=True,
        )

        try:
            self.processor = CLIPProcessor.from_pretrained(_CLIP_MODEL_NAME)
        except Exception:
            print(
                "[ImageSearchService] STEP 1a - FAILED loading CLIPProcessor:\n"
                + traceback.format_exc(),
                flush=True,
            )
            raise RuntimeError(
                "ImageSearchService: CLIPProcessor.from_pretrained() failed. "
                "Check Railway logs for full traceback. "
                "Ensure internet access or pre-cached model files."
            )

        print("[ImageSearchService] STEP 1a - CLIPProcessor loaded.", flush=True)

        # ------------------------------------------------------------------ #
        # STEP 1b — Load CLIPModel in float16 with low_cpu_mem_usage          #
        #                                                                      #
        # WHY float16:                                                         #
        #   CLIPModel in float32 = ~600 MB RAM                                #
        #   CLIPModel in float16 = ~300 MB RAM                                #
        #   Railway Starter plan has 512 MB total — float32 OOM-kills.        #
        #                                                                      #
        # WHY NOT SentenceTransformer:                                         #
        #   The FAISS index was built with CLIPModel.get_image_features(),     #
        #   not SentenceTransformer.encode(). Using the wrong loader produces  #
        #   mismatched query vectors and wrong search results.                 #
        #   SentenceTransformer also adds ~100 MB of wrapper overhead.        #
        # ------------------------------------------------------------------ #
        print(
            f"[ImageSearchService] STEP 1b - Loading CLIPModel (float16, low_cpu_mem_usage) "
            f"from '{_CLIP_MODEL_NAME}'...",
            flush=True,
        )

        try:
            self.model = CLIPModel.from_pretrained(
                _CLIP_MODEL_NAME,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
            )
            self.model.eval()
        except Exception:
            print(
                "[ImageSearchService] STEP 1b - FAILED loading CLIPModel:\n"
                + traceback.format_exc(),
                flush=True,
            )
            raise RuntimeError(
                "ImageSearchService: CLIPModel.from_pretrained() failed. "
                "Check Railway logs for full traceback."
            )

        print(
            f"[ImageSearchService] STEP 1b - CLIPModel loaded in eval/float16 mode.",
            flush=True,
        )

        # ------------------------------------------------------------------ #
        # STEP 2 — FAISS index                                                 #
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
                f"[ImageSearchService] STEP 2 - FAILED loading FAISS index:\n"
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
        # STEP 3 — Product ID mapping                                          #
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
                f"[ImageSearchService] STEP 3 - FAILED loading product IDs:\n"
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
        # STEP 4 — Alignment check                                             #
        # ------------------------------------------------------------------ #
        if self.index.ntotal != len(self.product_ids):
            msg = (
                f"[ImageSearchService] STEP 4 MISMATCH: "
                f"FAISS has {self.index.ntotal} vectors but "
                f"product_ids has {len(self.product_ids)} entries."
            )
            print(msg, flush=True)
            raise ValueError(msg)

        print(
            "[ImageSearchService] STEP 4 - ImageSearchService ready. "
            f"Serving {self.index.ntotal} products at dim={self.index.d}.",
            flush=True,
        )

    # ---------------------------------------------------------------------- #
    # search()                                                                 #
    # ---------------------------------------------------------------------- #
    def search(self, image_path, top_k=5):

        print(f"[ImageSearchService] Image received: {image_path}", flush=True)

        # ------------------------------------------------------------------ #
        # 1. Load image and run CLIP preprocessing                             #
        # ------------------------------------------------------------------ #
        try:
            with Image.open(image_path).convert("RGB") as image:

                # CLIPProcessor handles resizing, normalisation, and tensor
                # conversion — identical to what generate_image_embeddings.py did.
                inputs = self.processor(
                    images=image,
                    return_tensors="pt",
                )

                # ---------------------------------------------------------- #
                # 2. Extract image features — no_grad() prevents autograd     #
                #    graph accumulation (memory leak) across requests.         #
                #                                                              #
                # get_image_features() returns a plain tensor of shape        #
                # (1, 512) — the projected, unnormalised image embedding.     #
                #                                                              #
                # Convert inputs to float16 to match the model weights.       #
                # FAISS index was built from float32 — cast back after.       #
                # ---------------------------------------------------------- #
                with torch.no_grad():
                    inputs_fp16 = {
                        k: v.to(torch.float16) if v.dtype == torch.float32 else v
                        for k, v in inputs.items()
                    }
                    image_features = self.model.get_image_features(**inputs_fp16)

            # PIL image is now released (exited context manager)

            query_embedding = (
                image_features
                .cpu()
                .to(torch.float32)   # FAISS requires float32
                .numpy()
                .flatten()
            )

        except Exception:
            print(
                f"[ImageSearchService] FAILED during image encode:\n"
                + traceback.format_exc(),
                flush=True,
            )
            raise

        # Guarantee shape (1, dim) for FAISS
        query_embedding = query_embedding.reshape(1, -1).astype("float32")

        print(
            f"[ImageSearchService] Embedding shape: {query_embedding.shape} "
            f"(FAISS dim: {self.index.d})",
            flush=True,
        )

        if query_embedding.shape[1] != self.index.d:
            raise ValueError(
                f"[ImageSearchService] Embedding dim {query_embedding.shape[1]} "
                f"!= FAISS index dim {self.index.d}. "
                f"Model or preprocessing mismatch."
            )

        # ------------------------------------------------------------------ #
        # 3. FAISS search                                                      #
        # ------------------------------------------------------------------ #
        distances, indices = self.index.search(query_embedding, top_k)

        print(
            f"[ImageSearchService] FAISS search done. "
            f"indices={indices[0].tolist()}",
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

                # FAISS returns -1 for padding when results < top_k
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