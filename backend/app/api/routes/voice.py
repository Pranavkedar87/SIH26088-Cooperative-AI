"""
Hardware & Web Voice Endpoint Contract.

POST /api/voice/query

HARDWARE SECURITY ARCHITECTURE:
  - ESP32-S3 physical device communicates ONLY with this FastAPI endpoint.
  - ESP32-S3 NEVER holds GEMINI_API_KEY, SUPABASE_SERVICE_ROLE_KEY, or RAG logic.
  - This route accepts voice/audio input, runs STT, delegates to `services.query_service.process_user_query`,
    and returns text/audio response to the ESP32-S3 (for MAX98357A speaker playback).
"""
from __future__ import annotations
import logging
import os
import sys
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.schemas.query import QueryResponse, SourceItem

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))))

from services.query_service import process_user_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice", tags=["voice"])


class VoiceQueryRequest(BaseModel):
    transcript: Optional[str] = Field(
        default=None,
        description="Transcribed text from browser STT or ESP32-S3 microphone input.",
        examples=["PMFBY म्हणजे काय?"],
    )
    query: Optional[str] = Field(
        default=None,
        description="Alternative field name for transcribed text query.",
    )
    language: str = Field(
        default="en",
        description="ISO language code: en | hi | mr",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session UUID to maintain conversation history.",
    )
    response_mode: str = Field(
        default="voice",
        description="Response mode: 'voice' (concise spoken response) or 'text'.",
    )

    def get_text(self) -> str:
        text = self.transcript or self.query or ""
        return text.strip()


class VoiceQueryResponse(QueryResponse):
    audio_url: Optional[str] = Field(
        default=None,
        description="URL to generated audio file for MAX98357A speaker playback (populated when TTS is enabled).",
    )


@router.post("/query", response_model=VoiceQueryResponse)
async def voice_query(body: VoiceQueryRequest) -> VoiceQueryResponse:
    """
    Hardware & Web Voice Query Endpoint.

    Processes transcribed audio input through the central `process_user_query` AI/RAG pipeline.
    This ensures physical devices (ESP32) and web voice use the exact same AI brain.
    """
    try:
        query_text = body.get_text()
        if not query_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voice query text (transcript or query field) cannot be empty.",
            )

        logger.info("Voice Query received | device_id=%s | lang=%s | mode=%s | text=%.60s", body.device_id, body.language, body.response_mode, query_text)
        
        # Delegate directly to shared query service
        res = await process_user_query(
            message=query_text,
            language=body.language,
            session_id=body.session_id,
            response_mode=body.response_mode,
        )

        return VoiceQueryResponse(
            answer=res.answer,
            language=res.language,
            intent=res.intent,
            source=res.source,
            sources=res.sources,
            next_action=res.next_action,
            session_id=res.session_id,
            conversation_id=res.conversation_id,
            audio_url=None,  # TTS audio stream URL will be populated in future hardware task
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in /api/voice/query: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing voice request.",
        ) from exc

