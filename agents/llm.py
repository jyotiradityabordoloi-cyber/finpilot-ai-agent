import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()


def create_llm() -> ChatGroq:
    """
    Create the LLM used by FinPilot.

    The API key is loaded from the environment rather than
    being stored in source code.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Add it to the .env file."
        )

    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0,
        api_key=api_key,
    )