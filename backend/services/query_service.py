"""
Central shared AI query processing service.

This service is the SINGLE brain for processing user queries across ALL client interfaces:
  1. Web Application (text input via POST /api/query)
  2. Web Voice (browser voice STT -> process_user_query -> TTS)
  3. Physical AI Device (ESP32-S3 voice -> POST /api/voice/query -> STT -> process_user_query -> TTS)
  4. Camera / OCR (camera capture -> POST /api/vision/query -> OCR -> process_user_query)

SECURITY ARCHITECTURE:
  - Physical devices (ESP32) and web clients communicate ONLY with FastAPI.
  - ESP32-S3 NEVER holds GEMINI_API_KEY, SUPABASE_SERVICE_ROLE_KEY, or RAG logic.
  - All intent detection, vector search, Gemini generation, and DB storage are centralized here.
"""
from __future__ import annotations

import logging
from typing import Any, Optional, Tuple

from app.schemas.query import QueryRequest, QueryResponse, SourceItem
from rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)

# Singleton RAG pipeline instance
_rag_pipeline = RAGPipeline()


def _try_setup_db(session_id_from_request: str | None, language: str) -> Tuple[Optional[str], Optional[str]]:
    """Resolve or create a session + conversation. Never raises."""
    try:
        from database.repository import create_session, create_conversation

        if session_id_from_request:
            session_id = session_id_from_request
        else:
            session_id = create_session(language)

        conversation_id = None
        if session_id:
            conversation_id = create_conversation(session_id)

        return session_id, conversation_id

    except Exception as exc:
        logger.error("DB setup error in query_service (non-fatal): %s", exc)
        return None, None


def _try_save_message(
    conversation_id: Optional[str],
    role: str,
    content: str,
    language: str,
    intent: Optional[str] = None,
) -> None:
    """Save a single message to database (best-effort). Never raises."""
    if not conversation_id:
        return
    try:
        from database.repository import save_message
        save_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            language=language,
            intent=intent,
        )
    except Exception as exc:
        logger.error("Failed to persist message in query_service (role=%s): %s", role, exc)


async def process_user_query(
    message: str,
    language: str = "en",
    session_id: Optional[str] = None,
) -> QueryResponse:
    """
    Central AI processing entry point for ALL client interfaces (Web, ESP32 Voice, Vision).

    Flow:
      1. Setup/reuse session and conversation in Supabase (best-effort)
      2. Persist user message to database
      3. Execute RAG Pipeline (Intent -> Vector Retrieval -> Grounded Gemini)
      4. Persist assistant response to database
      5. Return structured QueryResponse with verified sources and session IDs

    Args:
        message: The user's input text (or transcribed speech / OCR text).
        language: Language code ("en", "hi", "mr").
        session_id: Optional UUID to maintain session context.

    Returns:
        QueryResponse containing answer, language, intent, sources, session_id, conversation_id.
    """
    clean_message = message.strip()

    # 1. DB setup (best-effort)
    res_session_id, conversation_id = _try_setup_db(session_id, language)

    # 2. Save user message (best-effort)
    _try_save_message(conversation_id, "user", clean_message, language)

    # 3. RAG Pipeline Execution
    req_obj = QueryRequest(
        message=clean_message,
        language=language, # type: ignore[arg-type]
        session_id=res_session_id,
    )

    rag_response, raw_sources = await _rag_pipeline.process_query(req_obj)

    # Convert raw sources to SourceItem objects
    source_items = [
        SourceItem(
            title=s["title"],
            source_name=s.get("source_name"),
            source_url=s.get("source_url"),
            document_id=s.get("document_id"),
        )
        for s in raw_sources
    ]

    # 4. Save assistant response (best-effort)
    _try_save_message(
        conversation_id,
        "assistant",
        rag_response.answer,
        rag_response.language,
        rag_response.intent,
    )

    # 5. Return complete structured response
    return QueryResponse(
        answer=rag_response.answer,
        language=rag_response.language,
        intent=rag_response.intent,
        source=rag_response.source,
        sources=source_items,
        next_action=rag_response.next_action,
        session_id=res_session_id,
        conversation_id=conversation_id,
    )
