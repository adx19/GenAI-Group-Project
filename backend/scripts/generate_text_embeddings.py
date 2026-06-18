import os
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

from app.database.session import SessionLocal
from app.models.product import Product

from app.models.product_attribute import ProductAttribute
from app.models.search_log import SearchLog
from app.models.search_click import SearchClick

MODEL_NAME = "sentence-transformers/all-MiniLM-l6-v2"

def mean_pooling(model_output, attention_mask):
  token_embeddings = model_output[0]
  input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
  return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def main():
  print("Loading embedding model...")
  tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
  model = AutoModel.from_pretrained(MODEL_NAME)
  model.eval()

  device = "cuda" if torch.cuda.is_available() else "cpu"
  model = model.to(device)

  db = SessionLocal()

  try:

    products = db.query(Product).all()

    print(f"Loaded {len(products)} products")
    product_ids = []
    texts = []
    for product in products:
      searchable_text = (f"{product.name} "
      f"{product.category}")
      product_ids.append(product.id)
      texts.append(searchable_text)

    print("Generating embeddings...")
    embeddings_list = []
    
    # Batch processing to prevent memory issues
    batch_size = 32
    for i in range(0, len(texts), batch_size):
      batch_texts = texts[i:i+batch_size]
      encoded_input = tokenizer(batch_texts, padding=True, truncation=True, return_tensors='pt').to(device)
      with torch.no_grad():
        model_output = model(**encoded_input)
        batch_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
        batch_embeddings = F.normalize(batch_embeddings, p=2, dim=1)
        embeddings_list.append(batch_embeddings.cpu().numpy())
      if (i // batch_size + 1) % 5 == 0:
        print(f"Processed {min(i + batch_size, len(texts))}/{len(texts)}")

    embeddings = np.vstack(embeddings_list)

    os.makedirs("embeddings/text", exist_ok=True)

    np.save("embeddings/text/product_ids.npy",np.array(product_ids))

    np.save("embeddings/text/text_embeddings.npy",embeddings)

    print("Embeddings saved successfully.")

    print(f"Shape: {embeddings.shape}")

  finally:
    db.close()


if __name__ == "__main__":
    main()