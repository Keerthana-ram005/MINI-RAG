from llm.gemini import ask_gemini
from llm.llama import ask_llama
from rag.retrieve import retrieve

# Priority order of LLMs
MODELS = [
    ("Gemini", ask_gemini),
    ("Llama", ask_llama),
]


def is_conversational(query: str) -> bool:
    """
    Returns True if the query is a simple greeting or a question about the bot's own identity.
    """
    q = query.strip("?!. ").lower()
    
    # Greetings
    if q in {
        "hi", "hello", "hey", "greetings", "good morning", "good afternoon",
        "good evening", "howdy", "sup", "yo", "hola", "namaste"
    }:
        return True
        
    # Identity / bot-info questions
    if q in {
        "tell me about yourself", "who are you", "what is your name", 
        "what are you", "describe yourself", "introduce yourself", "tell me abt yourself"
    }:
        return True
        
    return False


def build_prompt(query, context):
    """
    Build the prompt sent to the LLM.
    """

    if context:
        return f"""
You are a helpful AI assistant.

Answer the user's question ONLY using the provided context.

If the user's question is a simple greeting or pleasantry (like "hi", "hello", etc.), greet them back politely and ask how you can help, instead of saying you couldn't find it.

If the answer is not available in the context and it is a factual question, reply:
"I couldn't find that information in the knowledge base."

Context:
{context}

Question:
{query}

Answer:
"""

    return f"""
You are a helpful AI assistant.

No relevant knowledge base information was found.

Answer the following question using your general knowledge.

Question:
{query}

Answer:
"""


def ask_llm(query):
    """
    Retrieve context and query available LLMs in order.
    Falls back to the next model if one fails.
    """

    # If query is conversational (greeting or identity question), bypass retrieval
    if is_conversational(query):
        context = ""
    else:
        # Retrieve relevant documents from vector DB
        context = retrieve(query)

    # Build prompt
    prompt = build_prompt(query, context)

    errors = []

    for name, model in MODELS:
        try:
            print(f"Trying {name}...")

            response = model(prompt)

            if response and response.strip():
                print(f"{name} succeeded.")
                return response.strip()

            raise ValueError("Received empty response.")

        except Exception as e:
            error = f"{name} failed: {e}"
            print(error)
            errors.append(error)

    return (
        "Sorry, I couldn't generate a response.\n\n"
        + "\n".join(errors)
    )


def ask_llm_with_trace(query):
    """
    Retrieve context, query available LLMs in order, and track metadata traces.
    """
    sub_trace = {
        "retrieval": "N/A",
        "model_used": "None",
        "fallback_triggered": "No"
    }

    # If query is conversational (greeting or identity question), bypass retrieval
    if is_conversational(query):
        context = ""
        sub_trace["retrieval"] = "N/A"
    else:
        # Retrieve relevant documents from vector DB
        context = retrieve(query)
        sub_trace["retrieval"] = "Hit" if context.strip() else "Miss"

    # Build prompt
    prompt = build_prompt(query, context)

    errors = []

    for i, (name, model) in enumerate(MODELS):
        try:
            print(f"Trying {name}...")

            response = model(prompt)

            if response and response.strip():
                print(f"{name} succeeded.")
                sub_trace["model_used"] = name
                sub_trace["fallback_triggered"] = "Yes" if i > 0 else "No"
                return response.strip(), sub_trace

            raise ValueError("Received empty response.")

        except Exception as e:
            error = f"{name} failed: {e}"
            print(error)
            errors.append(error)

    sub_trace["fallback_triggered"] = "Yes" if len(MODELS) > 1 else "No"
    return (
        "Sorry, I couldn't generate a response.\n\n"
        + "\n".join(errors),
        sub_trace
    )