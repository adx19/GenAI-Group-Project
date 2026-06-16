import faiss
import numpy as np
import os

def main():
  print("Loading embeddings...")

  embeddings = np.load("embeddings/text/text_embeddings.npy")

  embeddings = embeddings.astype("float32")

  dimension = embeddings.shape[1]

  print(f"Dimension: {dimension}")


  index = faiss.IndexFlatL2(dimension)

  index.add(embeddings)

  os.makedirs("faiss_indexes", exist_ok=True)

  faiss.write_index(index, "faiss_indexes/text_index.faiss")

  print(f"Indexed {index.ntotal} vectors")

  print("Saved: faiss_indexes/text_index.faiss")


if __name__ == "__main__":
  main()