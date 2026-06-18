import os

import numpy as np
import torch
from PIL import Image
from torchvision import models


# ---------------------------------------------------------------------------
# EfficientNet-B0 configuration
#
# WHY EfficientNet-B0:
#   - 5.3 M parameters → ~21 MB RAM (vs CLIP ViT-B/32 at 151 M → ~576 MB)
#   - Ships inside torchvision — no HuggingFace download required
#   - Standard ImageNet weights downloaded once and cached (~21 MB)
#   - 1280-dim output (after removing classifier head)
#
# IMPORTANT: This model and dimension must exactly match image_search_service.py.
# If you change the model here you MUST regenerate embeddings AND the FAISS index.
# ---------------------------------------------------------------------------
IMAGE_DIR = "data/images"
OUTPUT_DIR = "embeddings/image"
EMBED_DIM = 1280          # EfficientNet-B0 avgpool output dimension


def load_model(device: str):
    """
    Load EfficientNet-B0 with ImageNet weights, strip the classifier head,
    and return (model, preprocess_transform).

    Removing the classifier replaces Linear(1280 → 1000) with Identity,
    so model(tensor) returns a (batch, 1280) embedding directly.
    """
    weights = models.EfficientNet_B0_Weights.DEFAULT
    model = models.efficientnet_b0(weights=weights)
    model.classifier = torch.nn.Identity()   # (batch, 1280) output
    model.eval()
    model.to(device)
    # weights.transforms() returns the official ImageNet preprocessing pipeline:
    # Resize(256) → CenterCrop(224) → ToTensor → Normalize(ImageNet stats)
    preprocess = weights.transforms()
    return model, preprocess


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    model, preprocess = load_model(device)
    print(f"EfficientNet-B0 loaded. Output embedding dim: {EMBED_DIM}")

    image_files = sorted(
        os.listdir(IMAGE_DIR),
        key=lambda x: int(os.path.splitext(x)[0])
    )
    print(f"Found {len(image_files)} images in {IMAGE_DIR}")

    image_embeddings = []
    product_ids = []
    failed = []

    for index, filename in enumerate(image_files):
        image_path = os.path.join(IMAGE_DIR, filename)
        try:
            with Image.open(image_path).convert("RGB") as img:
                tensor = preprocess(img).unsqueeze(0).to(device)  # (1, 3, 224, 224)

            with torch.no_grad():
                embedding = model(tensor).cpu().numpy().flatten()  # (1280,)

            image_embeddings.append(embedding)
            product_ids.append(int(os.path.splitext(filename)[0]))

            if (index + 1) % 100 == 0:
                print(f"  Processed {index + 1}/{len(image_files)}")

        except Exception as e:
            print(f"  Failed: {filename} — {e}")
            failed.append(filename)

    image_embeddings = np.array(image_embeddings, dtype=np.float32)
    product_ids = np.array(product_ids)

    # Sanity check: every embedding must have the expected dimension
    assert image_embeddings.shape[1] == EMBED_DIM, (
        f"Dimension mismatch: expected {EMBED_DIM}, got {image_embeddings.shape[1]}"
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    np.save(f"{OUTPUT_DIR}/image_embeddings.npy", image_embeddings)
    np.save(f"{OUTPUT_DIR}/image_product_ids.npy", product_ids)

    print(f"\nDone.")
    print(f"  Embeddings shape : {image_embeddings.shape}")
    print(f"  Products indexed : {len(product_ids)}")
    print(f"  Failed           : {len(failed)}")
    if failed:
        print(f"  Failed files     : {failed}")


if __name__ == "__main__":
    main()