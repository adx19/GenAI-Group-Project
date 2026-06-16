import os
import numpy as np
import torch

from PIL import Image
from transformers import CLIPProcessor
from transformers import CLIPModel


IMAGE_DIR = "data/images"

OUTPUT_DIR = "embeddings/image"

MODEL_NAME = "openai/clip-vit-base-patch32"


def main():

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(f"Using device: {device}")

    model = (
        CLIPModel
        .from_pretrained(MODEL_NAME)
        .to(device)
    )

    processor = (
        CLIPProcessor
        .from_pretrained(MODEL_NAME)
    )

    image_embeddings = []
    product_ids = []

    image_files = sorted(
        os.listdir(IMAGE_DIR),
        key=lambda x: int(
            os.path.splitext(x)[0]
        )
    )

    print(
        f"Found {len(image_files)} images"
    )

    for index, filename in enumerate(image_files):

        image_path = os.path.join(
            IMAGE_DIR,
            filename
        )

        try:

            image = (
                Image.open(image_path)
                .convert("RGB")
            )

            inputs = processor(
                images=image,
                return_tensors="pt"
            )

            inputs = {
                k: v.to(device)
                for k, v in inputs.items()
            }

            with torch.no_grad():

                outputs = (
                    model
                    .get_image_features(
                        **inputs
                    )
                )

            embedding = (
                outputs.pooler_output
                .cpu()
                .numpy()
                .flatten()
            )

            image_embeddings.append(
                embedding
            )

            product_ids.append(
                int(
                    os.path.splitext(
                        filename
                    )[0]
                )
            )

            if (index + 1) % 100 == 0:

                print(
                    f"Processed "
                    f"{index + 1}"
                )

        except Exception as e:

            print(
                f"Failed: "
                f"{filename}"
            )

            print(e)

    image_embeddings = np.array(
        image_embeddings,
        dtype=np.float32
    )

    product_ids = np.array(
        product_ids
    )

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    np.save(
        f"{OUTPUT_DIR}/image_embeddings.npy",
        image_embeddings
    )

    np.save(
        f"{OUTPUT_DIR}/image_product_ids.npy",
        product_ids
    )

    print("\nDone")

    print(
        f"Embeddings Shape: "
        f"{image_embeddings.shape}"
    )


if __name__ == "__main__":
    main()