"""
Query endpoint.

POST /api/query → QueryResponse

Delegates to the injected AIProvider — no direct AI calls here.
"""
from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.query import QueryRequest, QueryResponse
from app.dependencies import get_ai_provider
from app.providers.ai_provider import AIProvider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    provider: AIProvider = Depends(get_ai_provider),
) -> QueryResponse:
    """
    Accept a user question and return an AI-generated answer.

    - **message**: The user's question (1–2000 characters).
    - **language**: `en` | `hi` | `mr`
    """
    try:
        return await provider.answer_query(body)
    except Exception as exc:
        logger.exception("Unexpected error in /api/query: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request. Please try again.",
        ) from exc
