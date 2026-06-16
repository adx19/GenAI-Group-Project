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

        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        self.model = (
            CLIPModel
            .from_pretrained(
                "openai/clip-vit-base-patch32",
                local_files_only=True
            )   
            .to(self.device)
        )

        self.processor = (
            CLIPProcessor
            .from_pretrained(
                "openai/clip-vit-base-patch32",
                local_files_only=True
            )       
        )

        self.index = faiss.read_index(
            "faiss_indexes/image_index.faiss"
        )

        self.product_ids = np.load(
            "embeddings/image/image_product_ids.npy"
        )

    def search(
        self,
        image_path,
        top_k=5
    ):

        image = (
            Image.open(image_path)
            .convert("RGB")
        )

        inputs = self.processor(
            images=image,
            return_tensors="pt"
        )

        inputs = {
            k: v.to(self.device)
            for k, v in inputs.items()
        }

        with torch.no_grad():

            outputs = (
                self.model
                .get_image_features(
                    **inputs
                )
            )

            query_embedding = (
                outputs.pooler_output
                .cpu()
                .numpy()
                .astype("float32")
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