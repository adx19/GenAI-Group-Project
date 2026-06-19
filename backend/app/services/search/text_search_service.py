import faiss
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

import app.models
from app.models.product import Product
from app.models.enums import SearchType

from app.database.session import SessionLocal
from app.services.analytics.search_tracking_service import (SearchTrackingService)


class TextSearchService:
  def __init__(self):
    self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-l6-v2")
    self.model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-l6-v2")
    self.model.eval()

    self.index = faiss.read_index("faiss_indexes/text_index.faiss")
    self.product_ids = np.load("embeddings/text/product_ids.npy")

  def _mean_pooling(self, model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

  def search(self, query: str, top_k: int = 10):
    encoded_input = self.tokenizer([query], padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
      model_output = self.model(**encoded_input)
      query_embedding = self._mean_pooling(model_output, encoded_input['attention_mask'])
      query_embedding = F.normalize(query_embedding, p=2, dim=1)
      query_embedding = query_embedding.cpu().numpy()

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