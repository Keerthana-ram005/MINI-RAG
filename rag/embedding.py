from sentence_transformers import SentenceTransformer
from ingest import all_chunks

model = SentenceTransformer("all-MiniLM-L6-v2")  # fast, 384-dim

texts = [c["text"] for c in all_chunks]
embeddings = model.encode(texts, show_progress_bar=True)

from pymilvus import MilvusClient

client = MilvusClient("resume_rag.db")  # local file, Milvus Lite

try:
    client.drop_collection("resume_chunks")

except Exception as e:

    print("Drop skipped:", e)

client.create_collection(collection_name="resume_chunks", dimension=384)

print(client.list_collections())

data = [
    {
        "id": i,
        "vector": embeddings[i].tolist(),
        "text": all_chunks[i]["text"],
        "page_num": all_chunks[i]["page_num"],
        "source": all_chunks[i]["source"]
    }
    for i in range(len(all_chunks))
]

client.insert(collection_name="resume_chunks", data=data)

print(client.get_collection_stats("resume_chunks"))