"""
Web Query endpoint.

POST /api/query → QueryResponse

Delegates execution to the central shared service `services.query_service.process_user_query`.
This ensures identical RAG, intent, grounding, and persistence behavior across Web, Voice, and Hardware.
"""
from __future__ import annotations
import logging
import os
import sys

from fastapi import APIRouter, HTTPException, status
from app.schemas.query import QueryRequest, QueryResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))))

from services.query_service import process_user_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(body: QueryRequest) -> QueryResponse:
    """
    Accept a user text query and return a grounded RAG AI response with verified sources.

    - **message**: The user's question (1–2000 characters).
    - **language**: `en` | `hi` | `mr`
    - **session_id**: Optional session UUID.
    """
    try:
        return await process_user_query(
            message=body.message,
            language=body.language,
            session_id=body.session_id,
            response_mode=body.response_mode or "text",
        )
    except Exception as exc:
        logger.exception("Unexpected error in /api/query: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request. Please try again.",
        ) from exc
