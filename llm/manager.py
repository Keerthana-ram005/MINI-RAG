from llm.gemini import ask_gemini
from llm.llama import ask_llama
from rag.retrieve import retrieve

# Priority order of LLMs
MODELS = [
    ("Gemini", ask_gemini),
    ("Llama", ask_llama),
]


def build_prompt(query, context):
    """
    Build the prompt sent to the LLM.
    """

    if context:
        return f"""
You are a helpful AI assistant.

Answer the user's question ONLY using the provided context.

If the answer is not available in the context, reply:
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