"""
Abstract AI provider interface.

All AI providers (Gemini, OpenAI, etc.) must implement this protocol.
The FastAPI layer depends only on this abstraction — never on a concrete provider.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from app.schemas.query import QueryRequest, QueryResponse


class AIProvider(ABC):
    """
    Abstract base class for AI provider implementations.

    To add a new provider:
        1. Create a new file in app/providers/ (e.g. openai_provider.py).
        2. Subclass AIProvider and implement `answer_query`.
        3. Update app/dependencies.py to inject the new provider.
    """

    @abstractmethod
    async def answer_query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a user query and return a structured response.

        Args:
            request: The validated QueryRequest from the API layer.

        Returns:
            A QueryResponse with the AI-generated answer and metadata.
        """
        ...
