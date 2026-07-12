from pypdf import PdfReader
import requests
from bs4 import BeautifulSoup


def extract_text_by_page(pdf_path):
    reader = PdfReader(pdf_path)
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()

        if text and text.strip():
            pages.append({
                "page_num": i + 1,
                "text": text,
                "source": pdf_path
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