import sys
import os
from PIL import Image

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from app.api.search import get_text_service, get_image_service

def test_text():
    print("=== Testing Text Search ===")
    svc = get_text_service()
    res = svc.search("cotton shirt", top_k=3)
    print(f"Found {len(res)} text search results:")
    for r in res:
        print(f"  - Product: ID={r['product'].id}, Name={r['product'].name}, Score={r['score']:.4f}")

def test_image():
    print("=== Testing Image Search ===")
    svc = get_image_service()
    # Find the first image in data/images
    img_dir = "data/images"
    images = sorted(os.listdir(img_dir))
    if not images:
        print("No images found in data/images!")
        return
    img_path = os.path.join(img_dir, images[0])
    print(f"Using image: {img_path}")
    res = svc.search(img_path, top_k=3)
    print(f"Found {len(res)} image search results:")
    for r in res:
        print(f"  - Product: ID={r['product'].id}, Name={r['product'].name}, Score={r['score']:.4f}")

if __name__ == "__main__":
    test_text()
    test_image()
