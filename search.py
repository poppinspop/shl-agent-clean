import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("paraphrase-MiniLM-L3-v2")

index = faiss.read_index("shl_index.faiss", faiss.IO_FLAG_MMAP)

with open("metadata.pkl", "rb") as f:
    metadata = pickle.load(f)


def search_assessments(query, top_k=5):
    query_embedding = model.encode([query])
    query_embedding = np.array(query_embedding).astype("float32")

    distances, indices = index.search(query_embedding, top_k)

    results = []

    for idx in indices[0]:
        results.append(metadata[idx])

    return results


if __name__ == "__main__":
    query = input("Enter hiring query: ")

    results = search_assessments(query)

    print("\nTop recommendations:\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']}")
        print(f"URL: {result['url']}")
        print(f"Description: {result['description']}")
        print("-" * 50)
