import os
import numpy as np

from sentence_transformers import SentenceTransformer

from app.database.session import SessionLocal
from app.models.product import Product


from app.models.product_attribute import ProductAttribute
from app.models.search_log import SearchLog
from app.models.search_click import SearchClick

MODEL_NAME = "all-MiniLM-l6-v2"

def main():
  print("Loading embedding model...")

  model = SentenceTransformer(MODEL_NAME)

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

    embeddings = model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )

    os.makedirs("embeddings/text", exist_ok=True)

    np.save("embeddings/text/product_ids.npy",np.array(product_ids))

    np.save("embeddings/text/text_embeddings.npy",embeddings)

    print("Embeddings saved successfully.")

    print(f"Shape: {embeddings.shape}")

  finally:
    db.close()


if __name__ == "__main__":
    main()