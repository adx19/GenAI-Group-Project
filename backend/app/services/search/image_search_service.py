import faiss
import numpy as np

from PIL import Image
from sentence_transformers import SentenceTransformer

from app.services.analytics.search_tracking_service import SearchTrackingService
from app.models.enums import SearchType
from app.database.session import SessionLocal
from app.models.product import Product


class ImageSearchService:

    def __init__(self):

        print("[ImageSearchService] STEP 0 - Initializing ImageSearchService...")

        # ------------------------------------------------------------------ #
        # Model: SentenceTransformer with clip-ViT-B-32                       #
        # Produces 512-dimensional L2-normalized embeddings for PIL images.   #
        # Do NOT mix with CLIPModel / CLIPProcessor / get_image_features.     #
        # ------------------------------------------------------------------ #
        self.model = SentenceTransformer("clip-ViT-B-32")

        print("[ImageSearchService] STEP 1 - Model loaded (clip-ViT-B-32 via SentenceTransformer).")

        # ------------------------------------------------------------------ #
        # FAISS index                                                          #
        # ------------------------------------------------------------------ #
        self.index = faiss.read_index("faiss_indexes/image_index.faiss")

        print(
            f"[ImageSearchService] STEP 2 - FAISS index loaded. "
            f"Total vectors: {self.index.ntotal}, "
            f"Dimension: {self.index.d}"
        )

        # ------------------------------------------------------------------ #
        # Product ID mapping (parallel array to FAISS index rows)             #
        # ------------------------------------------------------------------ #
        self.product_ids = np.load(
            "embeddings/image/image_product_ids.npy",
            allow_pickle=False
        )

        print(
            f"[ImageSearchService] STEP 3 - Product IDs loaded. "
            f"Count: {len(self.product_ids)}"
        )

        # Sanity-check: FAISS vectors must equal product_ids entries
        if self.index.ntotal != len(self.product_ids):
            raise ValueError(
                f"[ImageSearchService] DIMENSION MISMATCH: "
                f"FAISS has {self.index.ntotal} vectors but "
                f"product_ids has {len(self.product_ids)} entries. "
                f"Re-run the indexing script to rebuild both files together."
            )

        print("[ImageSearchService] STEP 4 - ImageSearchService ready.")

    # ---------------------------------------------------------------------- #
    # search()                                                                 #
    # ---------------------------------------------------------------------- #
    def search(self, image_path, top_k=5):

        print(f"[ImageSearchService] Image received: {image_path}")

        # ------------------------------------------------------------------ #
        # 1. Load and preprocess the image                                    #
        # ------------------------------------------------------------------ #
        image = Image.open(image_path).convert("RGB")

        # ------------------------------------------------------------------ #
        # 2. Encode with SentenceTransformer                                  #
        #    - normalize_embeddings=True → L2-normalised float32 vectors      #
        #      which matches how the FAISS index was built during indexing.   #
        #    - convert_to_numpy=True → returns np.ndarray directly.           #
        # ------------------------------------------------------------------ #
        query_embedding = self.model.encode(
            image,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        # Guarantee shape is (1, dim) for FAISS
        if query_embedding.ndim == 1:
            query_embedding = np.expand_dims(query_embedding, axis=0)

        print(
            f"[ImageSearchService] Embedding shape: {query_embedding.shape} "
            f"(FAISS index dim: {self.index.d})"
        )

        # Guard: embedding dimension must match index
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
            f"Raw indices: {indices[0].tolist()}"
        )

        # ------------------------------------------------------------------ #
        # 4. Resolve product IDs and fetch from DB                            #
        # ------------------------------------------------------------------ #
        db = SessionLocal()

        try:
            results = []

            for idx, distance in zip(indices[0], distances[0]):

                # FAISS returns -1 when fewer than top_k results exist
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

            print(
                f"[ImageSearchService] Results returned: {len(results)}"
            )

            # ---------------------------------------------------------------- #
            # 5. Analytics tracking                                             #
            # ---------------------------------------------------------------- #
            tracker = SearchTrackingService()

            tracker.log_search(
                query=image_path,
                search_type=SearchType.IMAGE,
                results_count=len(results),
            )

            return results

        finally:
            db.close()