from tools.calculator import calculator
from tools.weather import get_weather
from tools.search import web_search

from llm.manager import ask_llm, ask_llm_with_trace
import time


def route_query(query: str):
    query_lower = query.lower()

    # Calculator
    if any(op in query_lower for op in ["+", "-", "*", "/", "calculate"]):
        return calculator(query)

    # Weather
    elif "weather" in query_lower:
        return get_weather(query)

    # Resume / RAG query has priority if it contains resume-related keywords
    elif any(word in query_lower for word in [
        "resume",
        "cv",
        "candidate",
        "experience",
        "skills",
        "education",
        "projects",
        "profile"
    ]):
        return ask_llm(query)

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


def route_query_with_trace(query: str):
    start_time = time.time()
    query_lower = query.lower()

    trace = {
        "retrieval": "N/A",
        "tool_used": "None",
        "model_used": "None",
        "fallback_triggered": "No",
        "response_time": 0.0
    }

    try:
        # Calculator
        if any(op in query_lower for op in ["+", "-", "*", "/", "calculate"]):
            trace["tool_used"] = "Calculator"
            response = calculator(query)

        # Weather
        elif "weather" in query_lower:
            trace["tool_used"] = "Weather"
            response = get_weather(query)

        # Resume / RAG query has priority if it contains resume-related keywords
        elif any(word in query_lower for word in [
            "resume",
            "cv",
            "candidate",
            "experience",
            "skills",
            "education",
            "projects",
            "profile"
        ]):
            trace["tool_used"] = "RAG"
            response, sub_trace = ask_llm_with_trace(query)
            trace.update(sub_trace)

        # Web Search
        elif any(word in query_lower for word in [
            "search",
            "find",
            "latest",
            "news",
            "google"
        ]):
            trace["tool_used"] = "Web Search"
            response = web_search(query)

        # Everything else
        else:
            from llm.manager import is_conversational
            if is_conversational(query):
                trace["tool_used"] = "Conversational"
            else:
                trace["tool_used"] = "Direct LLM"

            response, sub_trace = ask_llm_with_trace(query)
            trace.update(sub_trace)

    except Exception as e:
        response = f"An error occurred: {e}"

    trace["response_time"] = round(time.time() - start_time, 3)
    return response, trace