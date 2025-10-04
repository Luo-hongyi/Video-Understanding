import os
from openai import OpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def _get_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Please export your API key in environment variables.")
    return api_key


def get_openai_client() -> OpenAI:
    """Return OpenAI client initialized from environment."""
    return OpenAI(api_key=_get_api_key())


def get_chat_model(model: str = "gpt-4o", temperature: float = 0.5) -> ChatOpenAI:
    """Return LangChain ChatOpenAI client from environment settings."""
    return ChatOpenAI(model=model, temperature=temperature, api_key=_get_api_key())


def get_embeddings() -> OpenAIEmbeddings:
    """Return OpenAIEmbeddings initialized from environment."""
    return OpenAIEmbeddings(api_key=_get_api_key())

