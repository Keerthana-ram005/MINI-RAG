from tools.calculator import calculator
from tools.weather import get_weather
from tools.search import web_search

from llm.manager import ask_llm


def route_query(query: str):
    query_lower = query.lower()

    # Calculator
    if any(op in query_lower for op in ["+", "-", "*", "/", "calculate"]):
        return calculator(query)

    # Weather
    elif "weather" in query_lower:
        return get_weather(query)

    # Web Search
    elif any(word in query_lower for word in [
        "search",
        "find",
        "latest",
        "news",
        "google"
    ]):
        return web_search(query)

    # Everything else
    else:
        return ask_llm(query)