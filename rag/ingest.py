from pypdf import PdfReader
import requests
from bs4 import BeautifulSoup
import os
import re
from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient
import time


def is_spaced_out(text):
    """
    Detects if the text has spaced-out characters (letters separated by single spaces).
    """
    if not text:
        return False
    # Sample first 1000 characters
    sample = text[:1000].replace("\n", " ")
    words = [w for w in sample.split(" ") if w]
    if len(words) < 5:
        return False
    
    # Count single character words
    single_char_count = sum(1 for w in words if len(w) == 1)
    ratio = single_char_count / len(words)
    return ratio > 0.85


def clean_spaced_text(text):
    if not text:
        return ""
        
    spaced = is_spaced_out(text)
    print(f"DEBUG: is_spaced_out: {spaced}")
    if not spaced:
        return text

    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        # Split by two or more spaces
        parts = re.split(r' {2,}', line)
        cleaned_parts = []
        for part in parts:
            # Check if this specific part is spaced out (predominantly single characters)
            sub_words = [w for w in part.split(" ") if w]
            if sub_words:
                single_char_count = sum(1 for w in sub_words if len(w) == 1)
                part_ratio = single_char_count / len(sub_words)
                
                # If part is predominantly single characters, remove internal spaces
                if part_ratio > 0.75:
                    cleaned_part = part.replace(" ", "")
                else:
                    cleaned_part = part
            else:
                cleaned_part = part

            cleaned_part_str = cleaned_part.strip()
            if cleaned_part_str:
                cleaned_parts.append(cleaned_part_str)
        cleaned_lines.append(" ".join(cleaned_parts))
    return "\n".join(cleaned_lines)


def chunk_text(text, max_chars=1000, overlap=200):
    """
    Chunks text into smaller overlapping segments.
    """
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start += max_chars - overlap
        if max_chars <= overlap:
            break
    return chunks


def extract_text_by_page(pdf_path):
    reader = PdfReader(pdf_path)
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()

        if text and text.strip():
            # Clean spaced characters if they exist
            cleaned_text = clean_spaced_text(text)
            text_chunks = chunk_text(cleaned_text, max_chars=1000, overlap=200)
            for chunk in text_chunks:
                pages.append({
                    "page_num": i + 1,
                    "text": chunk,
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
        text_chunks = chunk_text(text, max_chars=1000, overlap=200)

        chunks = []
        for chunk in text_chunks:
            chunks.append({
                "page_num": None,
                "text": chunk,
                "source": url
            })
        return chunks

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
    print(f"DEBUG: Processing PDF '{filename}' containing {len(reader.pages)} pages...")
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            print(f"DEBUG: Page {i+1} raw text length: {len(text)}")
            cleaned_text = clean_spaced_text(text)
            print(f"DEBUG: Page {i+1} cleaned text length: {len(cleaned_text)}")
            text_chunks = chunk_text(cleaned_text, max_chars=1000, overlap=200)
            print(f"DEBUG: Page {i+1} generated {len(text_chunks)} chunks.")
            for chunk in text_chunks:
                chunks.append({
                    "page_num": i + 1,
                    "text": chunk,
                    "source": filename
                })
        else:
            print(f"DEBUG: Page {i+1} is empty or has no extractable text.")
    num_ingested = ingest_document(chunks)
    print(f"DEBUG: Successfully ingested {num_ingested} chunks from '{filename}'")
    return num_ingested


def ingest_url(url):
    chunks = extract_text_from_web(url)
    return ingest_document(chunks)