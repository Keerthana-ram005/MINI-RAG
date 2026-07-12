from ollama import chat


def ask_llama(prompt: str) -> str:
    """
    Sends the prompt to the local Llama model
    running in Ollama.
    """

    response = chat(
        model="llama3.2",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.message.content