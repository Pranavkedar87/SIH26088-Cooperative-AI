"""
FastAPI dependency injection.

Swap the provider here (or via config) to change the AI backend.
"""
from __future__ import annotations
from functools import lru_cache
from app.config import get_settings
from app.providers.ai_provider import AIProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.ollama_provider import OllamaProvider


@lru_cache(maxsize=1)
def get_ai_provider() -> AIProvider:
    """
    Return the application-wide AI provider singleton based on AI_PROVIDER config.
    """
    settings = get_settings()
    provider_name = (settings.ai_provider or "ollama").lower().strip()

    if provider_name == "ollama":
        return OllamaProvider()
    elif provider_name == "gemini":
        return GeminiProvider()

    # Default to OllamaProvider
    return OllamaProvider()
