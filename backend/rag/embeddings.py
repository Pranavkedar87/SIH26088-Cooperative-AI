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
        """Generate a single 768-dim embedding vector."""
        if not text or not text.strip():
            return [0.0] * EMBEDDING_DIMENSION

        client = self._get_client()
        try:
            res = client.models.embed_content(
                model=DEFAULT_EMBEDDING_MODEL,
                contents=text.strip(),
                config=genai_types.EmbedContentConfig(
                    output_dimensionality=EMBEDDING_DIMENSION
                ),
            )
            if res.embeddings and res.embeddings[0].values:
                return list(res.embeddings[0].values)
            logger.warning("Empty embedding returned for text snippet.")
            return [0.0] * EMBEDDING_DIMENSION
        except Exception as exc:
            logger.error("Failed to generate Gemini embedding: %s", exc)
            return [0.0] * EMBEDDING_DIMENSION

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of text snippets."""
        return [self.embed_text(t) for t in texts]
