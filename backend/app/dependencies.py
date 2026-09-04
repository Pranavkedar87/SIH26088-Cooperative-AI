"""
FastAPI dependency injection.

Swap the provider here (or via config) to change the AI backend.
"""
from __future__ import annotations
from functools import lru_cache
from app.providers.ai_provider import AIProvider
from app.providers.gemini_provider import GeminiProvider


@lru_cache(maxsize=1)
def get_ai_provider() -> AIProvider:
    """
    Return the application-wide AI provider singleton.

    In Milestone 2 this will read settings.AI_PROVIDER to decide which
    concrete provider to instantiate (Gemini, OpenAI, etc.).
    """
    return GeminiProvider()
