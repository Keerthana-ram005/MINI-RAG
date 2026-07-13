import requests
from duckduckgo_search import DDGS


def web_search(query, max_results=5):
    results = []

    # 1. Try DuckDuckGo first
    try:
        with DDGS() as ddgs:
            search_results = ddgs.text(query, max_results=max_results)
            for result in search_results:
                results.append({
                    "title": result.get("title", ""),
                    "body": result.get("body", ""),
                    "url": result.get("href", "")
                })
    except Exception as e:
        print(f"DEBUG: DuckDuckGo search failed: {e}")

    # 2. Fallback to Wikipedia API if standard web search fails/returns no results
    if not results:
        print("DEBUG: Web search returned 0 results. Falling back to Wikipedia API...")
        try:
            wiki_url = "https://en.wikipedia.org/w/api.php"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            # Step A: Search for matching article titles
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json"
            }
            res = requests.get(wiki_url, params=search_params, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                search_hits = data.get("query", {}).get("search", [])
                if search_hits:
                    titles = [hit["title"] for hit in search_hits[:max_results]]

                    # Step B: Fetch introductory text extracts for these pages
                    extract_params = {
                        "action": "query",
                        "prop": "extracts",
                        "exintro": 1,
                        "explaintext": 1,
                        "titles": "|".join(titles),
                        "format": "json"
                    }
                    res_extract = requests.get(wiki_url, params=extract_params, headers=headers, timeout=10)
                    if res_extract.status_code == 200:
                        extract_data = res_extract.json()
                        pages = extract_data.get("query", {}).get("pages", {})
                        for page_id, page_info in pages.items():
                            title = page_info.get("title", "")
                            extract = page_info.get("extract", "")
                            if title and extract.strip():
                                results.append({
                                    "title": title,
                                    "body": extract,
                                    "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                                })
        except Exception as e:
            print(f"DEBUG: Wikipedia fallback search failed: {e}")

    return results