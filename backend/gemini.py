from dotenv import load_dotenv
from google import genai
import os

load_dotenv("../.env")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3.6-flash"


def generate_answer(question, context):

    prompt = f"""
You are a helpful AI assistant for a document-based RAG chatbot.

Answer the user's question using ONLY the information provided
in the CONTEXT below.

If the answer cannot be found in the context, say:
"I couldn't find the answer in the uploaded documents."

Do not invent or assume information.

CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text


if __name__ == "__main__":

    answer = generate_answer(
        "What is binary search?",
        "Binary search is an efficient searching algorithm that works on sorted arrays."
    )

    print("\nGemini Answer:")
    print(answer)