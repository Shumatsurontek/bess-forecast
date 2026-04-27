"""LLM factory — plain LangChain ChatOpenAI, no provider abstraction."""
from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


def create_llm(model: str | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
        max_tokens=2000,
    )
