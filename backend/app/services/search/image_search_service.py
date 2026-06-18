from networkx.generators import spectral_graph_forge
from networkx.generators import spectral_graph_forge
import faiss
import numpy as np
import torch

from PIL import Image
from transformers import CLIPModel, CLIPProcessor
from app.services.analytics.search_tracking_service import (SearchTrackingService)

from app.models.enums import SearchType
from app.database.session import SessionLocal
from app.models.product import Product


class ImageSearchService:

    def __init__(self):

        print("STEP 0 - Starting ImageSearchService")

        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        print("STEP 1 - Before CLIPModel")

        self.model = SentenceTransformer(
            "clip-ViT-B-32"
        )

        print("STEP 3 - After CLIPProcessor")

        self.index = faiss.read_index(
            "faiss_indexes/image_index.faiss"
        )

        print("STEP 4 - After FAISS")

        self.product_ids = np.load(
            "embeddings/image/image_product_ids.npy"
        )

        print("STEP 5 - ImageSearchService Ready")

    def search(
        self,
        image_path,
        top_k=5
    ):

            image = Image.open(image_path).convert("RGB")

            query_embedding = self.model.encode(
                image,
                convert_to_numpy=True
            ).astype("float32")

            query_embedding = query_embedding.reshape(
                1,
                -1
            )
            
            distances, indices = (
                self.index.search(
                    query_embedding,
                    top_k
                )
            )

        db = SessionLocal()

        try:

            results = []

            for idx, distance in zip(indices[0],distances[0]):

                product_id = int(self.product_ids[idx])

                product = (
                    db.query(Product)
                    .filter(
                        Product.id == product_id
                    )
                    .first()
                )

                if product:
                    results.append({"product": product,"score": 1 / (1 + float(distance))})

            tracker = SearchTrackingService()
            
            search_log_id = tracker.log_search(
                query=image_path,
                search_type=SearchType.IMAGE,
                results_count=len(results)
            )
            
            return results

        finally:
            db.close()