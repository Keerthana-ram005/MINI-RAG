from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "resume_chunks"

client = MilvusClient("resume_rag.db")
client.load_collection(COLLECTION_NAME)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def retrieve(query, top_k=3):

    query_embedding = embedding_model.encode(query).tolist()

    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_embedding],
        limit=top_k,
        output_fields=["text", "page_num", "source"]
    )

    context = ""

    for hit in results[0]:

        # Skip weak matches
        if hit["distance"] > 0.6:
            continue

        entity = hit["entity"]

        print("Score:", hit["distance"])
        print("Source:", entity["source"])
        print("-" * 50)

        context += (
            f"Source: {entity['source']}\n"
            f"Page: {entity['page_num']}\n"
            f"{entity['text']}\n\n"
        )

    return context