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

        print("STEP 0 - Starting ImageSearchService")

        self.model = SentenceTransformer(
            "clip-ViT-B-32"
        )

        print("STEP 1 - Model Loaded")

        self.index = faiss.read_index(
            "faiss_indexes/image_index.faiss"
        )

        print("STEP 2 - FAISS Loaded")

        self.product_ids = np.load(
            "embeddings/image/image_product_ids.npy"
        )

        print("STEP 3 - Product IDs Loaded")

        print("STEP 4 - ImageSearchService Ready")

    def search(
        self,
        image_path,
        top_k=5
    ):

        image = (
            Image.open(image_path)
            .convert("RGB")
        )

        query_embedding = self.model.encode(
            image,
            convert_to_numpy=True
        ).astype("float32")

        query_embedding = np.expand_dims(
            query_embedding,
            axis=0
        )

        distances, indices = self.index.search(
            query_embedding,
            top_k
        )

        db = SessionLocal()

        try:

            results = []

            for idx, distance in zip(
                indices[0],
                distances[0]
            ):

                product_id = int(
                    self.product_ids[idx]
                )

                product = (
                    db.query(Product)
                    .filter(
                        Product.id == product_id
                    )
                    .first()
                )

                if product:
                    results.append(
                        {
                            "product": product,
                            "score": 1 / (
                                1 + float(distance)
                            )
                        }
                    )

            tracker = SearchTrackingService()

            tracker.log_search(
                query=image_path,
                search_type=SearchType.IMAGE,
                results_count=len(results)
            )

            return results

        finally:
            db.close()