"""
Embedding provider abstraction and Gemini implementation.

Generates 768-dimensional embeddings suitable for Supabase pgvector storage.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from google import genai
from google.genai import types as genai_types

from app.config import get_settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSION = 768
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"


class EmbeddingProvider(ABC):
    """Abstract base class for vector embedding providers."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate vector embedding for a text string."""
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a list of text strings."""
        ...


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Concrete Gemini implementation of EmbeddingProvider.
    Uses `gemini-embedding-001` configured to 768 output dimensions.
    """

    _client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if GeminiEmbeddingProvider._client is None:
            settings = get_settings()
            api_key = settings.gemini_api_key.strip()
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY is not configured in backend/.env")
            GeminiEmbeddingProvider._client = genai.Client(api_key=api_key)
        return GeminiEmbeddingProvider._client

    def embed_text(self, text: str) -> list[float]:
        """Generate a single 768-dim embedding vector via REST API with 2s timeout."""
        if not text or not text.strip():
            return [0.0] * EMBEDDING_DIMENSION

        import json as _json
        import urllib.request as _urllib_req
        import os

        settings = get_settings()
        api_key = (settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        if not api_key:
            return [0.0] * EMBEDDING_DIMENSION

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{DEFAULT_EMBEDDING_MODEL}:embedContent?key={api_key}"
            body = {
                "content": {"parts": [{"text": text.strip()[:500]}]},
                "outputDimensionality": EMBEDDING_DIMENSION,
            }
            req = _urllib_req.Request(
                url,
                data=_json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with _urllib_req.urlopen(req, timeout=2.0) as resp:
                data = _json.loads(resp.read().decode("utf-8"))
                values = data.get("embedding", {}).get("values", [])
                if values:
                    return list(values)
        except Exception as exc:
            logger.debug("Fast embedding fallback: %s", exc)

        return [0.0] * EMBEDDING_DIMENSION

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of text snippets."""
        return [self.embed_text(t) for t in texts]
