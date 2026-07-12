from pypdf import PdfReader
import requests
from bs4 import BeautifulSoup

def extract_text_by_page(pdf_path):
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append({"page_num": i + 1, "text": text, "source": pdf_path})
    return pages

def extract_text_from_web(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(separator=" ", strip=True)

    return [
        {
            "page_num": None,
            "text": text,
            "source": url
        }
    ]

documents = []

# PDF
documents.extend(extract_text_by_page("RESUME.pdf"))

# Website
documents.extend(
    extract_text_from_web("https://lyfngo.com/")
)

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

all_chunks = []

for doc in documents:
    chunks = chunk_text(doc["text"])

    for chunk in chunks:
        all_chunks.append({
            "text": chunk,
            "page_num": doc["page_num"],
            "source": doc["source"]
        })