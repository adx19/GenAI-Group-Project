import faiss
import numpy as np
import os


def main():

    embeddings = np.load(
        "embeddings/image/image_embeddings.npy"
    )

    embeddings = embeddings.astype(
        "float32"
    )

    dimension = embeddings.shape[1]

    print(
        f"Dimension: {dimension}"
    )

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(embeddings)

    os.makedirs(
        "faiss_indexes",
        exist_ok=True
    )

    faiss.write_index(
        index,
        "faiss_indexes/image_index.faiss"
    )

    print(
        f"Indexed {index.ntotal} images"
    )


if __name__ == "__main__":
    main()