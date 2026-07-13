from tools.calculator import calculator
from tools.weather import get_weather
from tools.search import web_search

from llm.manager import ask_llm, ask_llm_with_trace
import time
import re


def is_math_query(query: str) -> bool:
    """
    Returns True if the query is a mathematical question or calculation expression.
    """
    query_lower = query.lower().strip()

    # If it starts with 'calculate'
    if query_lower.startswith("calculate"):
        return True

    # If it is a pure math expression
    clean_q = re.sub(r"\s+", "", query)
    if re.match(r"^[0-9+\-*/().]+$", clean_q) and any(op in clean_q for op in ["+", "-", "*", "/"]):
        # Exclude dates (e.g. YYYY-MM-DD or MM-DD-YYYY)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", clean_q) or re.match(r"^\d{2}-\d{2}-\d{4}$", clean_q):
            return False
        return True

    # If it asks 'what is <math expression>'
    if query_lower.startswith("what is ") or query_lower.startswith("what's "):
        expr = query_lower.replace("what is", "").replace("what's", "").strip("? ")
        clean_expr = re.sub(r"\s+", "", expr)
        if re.match(r"^[0-9+\-*/().]+$", clean_expr) and any(op in clean_expr for op in ["+", "-", "*", "/"]):
            return True

    return False


def classify_query(query: str) -> str:
    """
    Classifies the user query category using the primary LLM with fallback.
    """
    prompt = f"""
Classify the following user query into exactly one of these categories:
- "conversational": simple greetings, pleasantries, or questions asking who you are.
- "calculator": mathematical expressions or calculations.
- "weather": queries asking about current weather or forecast.
- "rag": questions asking about the uploaded documents, PDFs, papers, resumes, portfolio, or candidate's projects/skills.
- "general": general knowledge, definitions, history, concepts, or general facts (e.g. "what is docker", "tell me about tata group").

User Query: "{query}"

Category (reply with ONLY the category name):
"""
    try:
        from llm.manager import MODELS
        for name, model in MODELS:
            try:
                category = model(prompt).strip().lower().replace('"', '').replace('.', '').strip()
                if category in {"conversational", "calculator", "weather", "rag", "general"}:
                    return category
            except Exception:
                continue
    except Exception:
        pass
    
    # Fallback heuristics
    query_lower = query.lower()
    if is_math_query(query):
        return "calculator"
    if "weather" in query_lower:
        return "weather"
    from llm.manager import is_conversational
    if is_conversational(query):
        return "conversational"
    if any(word in query_lower for word in ["resume", "cv", "candidate", "experience", "skills", "education", "projects", "profile", "paper", "author", "ijcrt"]):
        return "rag"
        
    return "general"


def route_query(query: str):
    response, trace = route_query_with_trace(query)
    return response


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
        from llm.manager import ask_llm_with_trace
        from rag.retrieve import retrieve

        # 1. Classify intent
        category = classify_query(query)
        print(f"DEBUG: Classified query category: '{category}'")

        # 2. Conversational Route
        if category == "conversational":
            trace["retrieval"] = "N/A"
            trace["tool_used"] = "Conversational"
            response, sub_trace = ask_llm_with_trace(query, context="")
            trace.update(sub_trace)

        # 3. Calculator Route
        elif category == "calculator":
            trace["retrieval"] = "N/A"
            trace["tool_used"] = "Calculator"
            response = calculator(query)

        # 4. Weather Route
        elif category == "weather":
            trace["retrieval"] = "N/A"
            trace["tool_used"] = "Weather"
            response = get_weather(query)

        # 5. General LLM Route (No RAG / Vector DB)
        elif category == "general":
            trace["retrieval"] = "N/A"
            trace["tool_used"] = "Direct LLM"
            response, sub_trace = ask_llm_with_trace(query, context="")
            trace.update(sub_trace)

        # 6. RAG Route (Vector DB)
        else:
            db_context = retrieve(query)
            if db_context.strip():
                # RAG path - relevant context is found in knowledge base
                trace["retrieval"] = "Hit"
                trace["tool_used"] = "RAG"
                response, sub_trace = ask_llm_with_trace(query, context=db_context)
                trace.update(sub_trace)
            else:
                # Miss - no relevant context, fallback to Web Search
                trace["retrieval"] = "Miss"
                trace["tool_used"] = "Web Search"
                web_results = web_search(query)
                
                if web_results:
                    context_from_web = "\n\n".join([
                        f"Title: {r['title']}\nSource: {r['url']}\nContent: {r['body']}"
                        for r in web_results
                    ])
                    response, sub_trace = ask_llm_with_trace(query, context=context_from_web, from_web=True)
                    trace.update(sub_trace)
                else:
                    response = "I couldn't find any information."

    except Exception as e:
        response = f"An error occurred: {e}"

    trace["response_time"] = round(time.time() - start_time, 3)
    return response, trace