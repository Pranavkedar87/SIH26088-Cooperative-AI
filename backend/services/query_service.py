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

import asyncio
import logging
import uuid
from typing import Any, Optional, Tuple

from app.schemas.query import QueryRequest, QueryResponse, SourceItem
from rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)

# Singleton RAG pipeline instance
_rag_pipeline = RAGPipeline()


def _async_persist_chat_history(
    session_id: str,
    conversation_id: str,
    user_message: str,
    assistant_answer: str,
    language: str,
    intent: Optional[str] = None,
) -> None:
    """Background worker to save session, conversation, user msg, and assistant msg to Supabase."""
    try:
        from database.repository import create_session, create_conversation, save_message

        # Ensure session and conversation exist in DB
        s_id = create_session(language) or session_id
        c_id = create_conversation(s_id) or conversation_id

        # Save user and assistant turns
        save_message(
            conversation_id=c_id,
            role="user",
            content=user_message,
            language=language,
        )
        save_message(
            conversation_id=c_id,
            role="assistant",
            content=assistant_answer,
            language=language,
            intent=intent,
        )
    except Exception as exc:
        logger.error("Background DB persistence error (non-fatal): %s", exc)


async def process_user_query(
    message: str,
    language: str = "mr",
    session_id: Optional[str] = None,
    response_mode: str = "text",
) -> QueryResponse:
    """
    Central AI processing entry point for ALL client interfaces (Web, ESP32 Voice, Vision).
    Optimized for high speed: RAG executes immediately while DB persistence runs in background.
    """
    clean_message = message.strip()

    # 1. Instant session and conversation ID generation
    res_session_id = session_id or str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())

    # 2. RAG Pipeline Execution (Immediate)
    req_obj = QueryRequest(
        message=clean_message,
        language=language,  # type: ignore[arg-type]
        session_id=res_session_id,
        response_mode=response_mode,  # type: ignore[arg-type]
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

    # 3. Schedule DB persistence in background task without blocking response delivery
    try:
        loop = asyncio.get_running_loop()
        loop.run_in_executor(
            None,
            _async_persist_chat_history,
            res_session_id,
            conversation_id,
            clean_message,
            rag_response.answer,
            language,
            rag_response.intent,
        )
    except Exception as exc:
        logger.error("Failed to schedule background DB persistence: %s", exc)

    # 4. Return complete structured response immediately
    return QueryResponse(
        answer=rag_response.answer,
        display_answer=rag_response.display_answer,
        spoken_answer=rag_response.spoken_answer,
        language=language,  # type: ignore[arg-type]
        intent=rag_response.intent,
        answer_focus=getattr(rag_response, "answer_focus", "OVERVIEW"),
        source=rag_response.source,
        sources=source_items,
        next_action=rag_response.next_action,
        session_id=res_session_id,
        conversation_id=conversation_id,
    )

