"""
Conversations endpoint.

GET /api/conversations/{conversation_id}/messages
  → List of messages in chronological order.
"""
from __future__ import annotations
import logging
import os
import sys

from fastapi import APIRouter, HTTPException, status
from app.schemas.query import MessageItem

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))))

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["conversations"])


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageItem],
)
async def get_messages(conversation_id: str) -> list[MessageItem]:
    """
    Return all messages for a conversation in chronological order.

    - **conversation_id**: UUID returned from POST /api/query
    """
    try:
        from database.repository import get_conversation_messages
        rows = get_conversation_messages(conversation_id)
        return [
            MessageItem(
                role=r["role"],
                content=r["content"],
                language=r["language"],
                intent=r.get("intent"),
            )
            for r in rows
        ]
    except Exception as exc:
        logger.error("Error fetching messages for %s: %s", conversation_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve conversation history.",
        ) from exc
