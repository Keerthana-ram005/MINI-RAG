from pypdf import PdfReader
import requests
from bs4 import BeautifulSoup
import os
import re
from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient
import time


def clean_spaced_text(text):
    if not text:
        return ""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        # Split by two or more spaces
        parts = re.split(r' {2,}', line)
        cleaned_parts = []
        for part in parts:
            cleaned_part = part.replace(" ", "")
            if cleaned_part:
                cleaned_parts.append(cleaned_part)
        cleaned_lines.append(" ".join(cleaned_parts))
    return "\n".join(cleaned_lines)


def extract_text_by_page(pdf_path):
    reader = PdfReader(pdf_path)
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()

        if text and text.strip():
            # Clean spaced characters if they exist
            cleaned_text = clean_spaced_text(text)
            pages.append({
                "page_num": i + 1,
                "text": cleaned_text,
                "source": os.path.basename(pdf_path)
            })

    return pages


def extract_text_from_web(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove unwanted elements
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        return [{
            "page_num": None,
            "text": text,
            "source": url
        }]

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []


# Build and export all_chunks
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf_path = os.path.join(base_dir, "RESUME.pdf")

pdf_chunks = extract_text_by_page(pdf_path)
web_chunks = extract_text_from_web("https://lyfngo.com/")
all_chunks = pdf_chunks + web_chunks


def ingest_document(chunks):
    """
    Ingests a list of chunks into Milvus.
    Each chunk is a dict: {'text': str, 'page_num': int/None, 'source': str}
    """
    if not chunks:
        return 0

    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = MilvusClient("resume_rag.db")

    # Generate embeddings
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts)

    data = []
    base_id = time.time_ns()
    for i, chunk in enumerate(chunks):
        data.append({
            "id": base_id + i,
            "vector": embeddings[i].tolist(),
            "text": chunk["text"],
            "page_num": chunk["page_num"],
            "source": chunk["source"]
        })

    client.insert(collection_name="resume_chunks", data=data)
    # Ensure collection is loaded
    client.load_collection("resume_chunks")
    return len(chunks)


def ingest_pdf_file(file_obj, filename):
    reader = PdfReader(file_obj)
    chunks = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            cleaned_text = clean_spaced_text(text)
            chunks.append({
                "page_num": i + 1,
                "text": cleaned_text,
                "source": filename
            })
    return ingest_document(chunks)


def ingest_url(url):
    chunks = extract_text_from_web(url)
    return ingest_document(chunks)