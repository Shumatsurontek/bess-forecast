import os

from langchain_openai import ChatOpenAI


def create_llm(model: str | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        temperature=0,
        max_tokens=2000,
    )
