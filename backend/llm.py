import os
import time

from google import genai
from dotenv import load_dotenv


# ==========================================
# Load environment variables
# ==========================================

load_dotenv("../.env")


# ==========================================
# Gemini Client
# ==========================================

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set in the .env file"
    )


client = genai.Client(
    api_key=API_KEY
)


# ==========================================
# Gemini Model
# ==========================================

MODEL_NAME = "gemini-3.6-flash"


# ==========================================
# Rewrite follow-up question
# ==========================================

def rewrite_question(history, question):
    """
    Convert a follow-up question into a standalone
    question using the previous conversation.
    """

    if not history:
        return question

    conversation = ""

    for message in history[-6:]:
        role = message.get("role", "")
        text = message.get("content") or message.get("text", "")

        if text:
            conversation += f"{role}: {text}\n"

    prompt = f"""
You are helping a RAG chatbot search uploaded documents.

Rewrite the user's latest question into a standalone
search query using the conversation history.

Rules:

1. Preserve the user's original meaning.
2. Resolve words such as:
   - it
   - its
   - they
   - them
   - this
   - that
   using the conversation history.
3. Do not answer the question.
4. Do not add information that is not present in the conversation.
5. If the question is already standalone, return it unchanged.
6. Return ONLY the rewritten question.

CONVERSATION HISTORY:

{conversation}

LATEST USER QUESTION:

{question}

STANDALONE SEARCH QUESTION:
"""

    try:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        if response and response.text:

            rewritten = response.text.strip()

            # Remove accidental quotes
            rewritten = rewritten.strip('"').strip("'")

            return rewritten

    except Exception as e:

        print(
            f"Question rewriting failed: {e}"
        )

    # If rewriting fails, use original question
    return question


# ==========================================
# Generate Answer
# ==========================================

def generate_answer(
    context,
    question,
    history=None
):

    if history is None:
        history = []


    # ==========================================
    # Build conversation history
    # ==========================================

    history_text = ""

    for message in history:

        role = message.get("role", "")
        content = message.get("content", "")

        if not content:
            continue

        if role == "user":

            history_text += (
                f"User: {content}\n"
            )

        elif role == "assistant":

            history_text += (
                f"Assistant: {content}\n"
            )


    # ==========================================
    # If there is no history
    # ==========================================

    if not history_text:

        history_text = "No previous conversation."


    # ==========================================
    # Gemini Prompt
    # ==========================================

    prompt = f"""
You are an educational RAG chatbot.

Your job is to answer the user's question using the
currently selected uploaded document.

IMPORTANT RULES:

1. Use the document context as the primary source.

2. Answer questions using information from the current document.

3. The retrieved context may contain facts that answer the question
indirectly. You may make simple logical conclusions from those facts,
but do not introduce unsupported external knowledge.

4. Do NOT mix information from other PDF documents.

5. Use the conversation history to understand follow-up questions.

6. Resolve pronouns and references using the conversation history.

For example:

User: What is a heap?

Assistant: A heap is a complete binary tree...

User: What is its time complexity?

Assistant: The word "its" refers to the heap discussed previously.

7. If the current question is a follow-up question, use the
previous conversation to understand what the user is referring to.

8. Do not use information from another document.

9. If the document does not explicitly list the requested information,
but the retrieved document context contains enough facts to logically
derive the answer, explain the answer using only those facts.

For example, if the document states that an algorithm:
- runs in O(n log n),
- works in-place,
- or can sort in ascending and descending order,

you may present these as advantages when the user asks for advantages.

Do NOT add advantages from general knowledge unless they are supported
by the retrieved document context.

Only say:

"I could not find enough information in the uploaded document."

when the retrieved context genuinely does not provide enough information
to answer the question.

10. Keep answers clear and easy to understand.

11. Keep answers concise unless an explanation is required.

12. For algorithm and data-structure questions, include relevant
definitions, steps and complexity information when available
in the document.

13. For time-complexity questions, provide Big-O notation when
supported by the document.

14. Do not mention the conversation history in your answer unless
the user explicitly asks about it.


==========================================
CONVERSATION HISTORY
==========================================

{history_text}


==========================================
CURRENT DOCUMENT CONTEXT
==========================================

{context}


==========================================
CURRENT USER QUESTION
==========================================

{question}


==========================================
ANSWER
==========================================
"""


    # ==========================================
    # Retry Gemini
    # ==========================================

    max_retries = 3

    for attempt in range(max_retries):

        try:

            print(
                f"Sending request to Gemini "
                f"(attempt {attempt + 1}/{max_retries})..."
            )


            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )


            # ==========================================
            # Check response
            # ==========================================

            if response and response.text:

                return response.text.strip()


            return (
                "I could not generate an answer "
                "from the uploaded document."
            )


        except Exception as e:

            error_message = str(e)

            print(
                f"Gemini error on attempt "
                f"{attempt + 1}: {error_message}"
            )


            # ==========================================
            # Handle 503
            # ==========================================

            if (
                "503" in error_message
                or "UNAVAILABLE" in error_message
            ):

                if attempt < max_retries - 1:

                    wait_time = 2 ** attempt

                    print(
                        f"Gemini temporarily unavailable. "
                        f"Retrying in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                    continue


                return (
                    "Gemini is temporarily unavailable because "
                    "the model is experiencing high demand. "
                    "Please try again in a few seconds."
                )


            # ==========================================
            # Handle 404
            # ==========================================

            if (
                "404" in error_message
                or "NOT_FOUND" in error_message
            ):

                return (
                    "The configured Gemini model is unavailable. "
                    "Please check the Gemini model name."
                )


            # ==========================================
            # Other errors
            # ==========================================

            return (
                "Unable to generate an answer right now. "
                "Please try again."
            )