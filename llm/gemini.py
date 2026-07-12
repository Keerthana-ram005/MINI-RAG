from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_response(prompt):
    """
    Sends a prompt to Gemini and returns the response.
    """

    response = client.models.generate_content(
        GEMINI_MODEL,
        contents=prompt
    )

    return response.text