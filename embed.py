import json
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

# load scraped catalog
with open("catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")

documents = []
metadata = []

for item in catalog:
    text = f"""
    Name: {item.get('name', '')}
    Description: {item.get('description', '')}
    Job Levels: {item.get('job_levels', '')}
    Test Type: {item.get('test_type', '')}
    """

    documents.append(text)
    metadata.append(item)

print(f"Embedding {len(documents)} assessments...")

embeddings = model.encode(documents)

embeddings = np.array(embeddings).astype("float32")

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

faiss.write_index(index, "shl_index.faiss")

with open("metadata.pkl", "wb") as f:
    pickle.dump(metadata, f)

print("Saved embeddings + metadata")
