import pandas as pd

from app.database.session import SessionLocal
from app.models.product import Product
from app.models.product_attribute import ProductAttribute
from app.models.search_log import SearchLog
from app.models.search_click import SearchClick

def main():
  print("Loading dataset...")

  df = pd.read_csv("data/processed/products_sample.csv")

  db = SessionLocal()

  inserted= 0
  skipped = 0

  try:
    for _, row in df.iterrows():

      existing_product = (db.query(Product).filter(Product.asin == row["asin"]).first())

      if existing_product:
        skipped += 1
        continue
      product = Product(
        asin=row["asin"],
        name=row["title"],
        category=row["category_name"],
        description=None,
        image_url=row["imgUrl"],
        price=float(row["price"]) if pd.notna(row["price"]) else None,
        rating=float(row["stars"]) if pd.notna(row["stars"]) else None,
        is_best_seller=bool(row["isBestSeller"])
      )

      db.add(product)
      inserted +=1
    db.commit()

    print(f"Inserted: {inserted}")
    print(f"Skipped: {skipped}")

  except Exception as e:
    db.rollback()
    raise e
  finally:
    db.close()


if __name__ == "__main__":
  main()