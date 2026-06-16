import os
import requests

from app.database.session import SessionLocal
from app.models.product import Product

from app.models.product_attribute import ProductAttribute
from app.models.search_log import SearchLog
from app.models.search_click import SearchClick

SAVE_DIR = "data/images"

def download_image(url, path):

  try:
    response = requests.get(url, timeout=10)

    if response.status_code == 200:
      with open(path, "wb") as file:
        file.write(response.content)

      return True
  except Exception:
    pass
  
  return False


def main():
  os.makedirs(SAVE_DIR, exist_ok=True)

  db = SessionLocal()

  products = db.query(Product).all()

  downloaded = 0

  failed = 0

  try:
    for product in products:
      image_path = (f"{SAVE_DIR}/{product.id}.jpg")

      if os.path.exists(image_path):
        continue
      
      success = download_image(product.image_url, image_path)

      if success:
        downloaded += 1
      else:
        failed += 1
      if downloaded % 100 == 0 and downloaded > 0:
        print(f"Downloaded: {downloaded}")
    print("\nFinished")

    print(f"Downloaded: {downloaded}")
    print(f"failed: {failed}")
  finally:
    db.close()

if __name__ == "__main__":
  main()