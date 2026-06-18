import faiss
import numpy as np
import app.models
from app.models.product import Product
from app.models.enums import SearchType
from sentence_transformers import SentenceTransformer

from app.database.session import SessionLocal
from app.services.analytics.search_tracking_service import (SearchTrackingService)



class TextSearchService:
  def __init__(self):

    self.model = SentenceTransformer("all-MiniLM-l6-v2")

    self.index = faiss.read_index("faiss_indexes/text_index.faiss")

    self.product_ids = np.load("embeddings/text/product_ids.npy")

  def search(self, query: str, top_k: int = 10):
    query_embedding = self.model.encode([query])

    query_embedding = query_embedding.astype("float32")

    distances, indices = self.index.search(query_embedding, top_k)

    db = SessionLocal()

    try:

      results = []

      for idx, distance in zip(indices[0],distances[0]):
        product_id = int(self.product_ids[idx])

        product = (db.query(Product).filter(Product.id == product_id).first())

        if product:
          results.append({"product": product,"score": 1 / (1 + float(distance))})
      tracker = SearchTrackingService()
      tracker.log_search(query=query, search_type=SearchType.TEXT,results_count=len(results))
      return results
    
    finally:
      db.close()