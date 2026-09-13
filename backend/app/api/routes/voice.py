"""
Hardware & Web Voice Endpoint Contract.

POST /api/voice/query
POST /api/voice/transcribe

HARDWARE & WEB VOICE SECURITY ARCHITECTURE:
  - ESP32-S3 physical device and browser frontend communicate ONLY with FastAPI endpoints.
  - Physical devices and browsers NEVER hold GROQ_API_KEY.
  - `/transcribe` runs server-side STT via Groq Whisper (`whisper-large-v3-turbo`).
  - `/query` accepts transcribed text or processes query through central RAG/AI pipeline.
"""
from __future__ import annotations
import logging
import os
import sys
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel, Field
from app.schemas.query import QueryResponse, SourceItem
from app.providers.stt_provider import HybridSTTProvider
from app.providers.bhashini_provider import BhashiniProvider

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))))

from services.query_service import process_user_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice", tags=["voice"])

hybrid_stt_provider = HybridSTTProvider()
bhashini_tts_provider = BhashiniProvider()


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
    device_id: Optional[str] = Field(
        default=None,
        description="Optional physical device hardware identifier.",
    )

    def get_text(self) -> str:
        text = self.transcript or self.query or ""
        return text.strip()


class VoiceQueryResponse(QueryResponse):
    audio_url: Optional[str] = Field(
        default=None,
        description="URL to generated audio file for MAX98357A speaker playback (populated when TTS is enabled).",
    )


class TranscribeResponse(BaseModel):
    transcript: str = Field(..., description="Transcribed text string from server-side STT.")
    language: str = Field(..., description="Language ISO code used for STT.")
    confidence: float = Field(default=0.98, description="STT confidence score.")
    provider: str = Field(default="groq_whisper", description="STT provider identifier.")
    latency_ms: float = Field(default=0.0, description="STT processing latency in milliseconds.")


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form("en"),
    session_id: Optional[str] = Form(None),
) -> TranscribeResponse:
    """
    Multilingual Audio Transcription Endpoint.

    Receives raw audio file from browser MediaRecorder / microphone, runs Groq Whisper
    transcription for English, Hindi, Marathi, and other supported languages, and returns
    the transcribed text string.
    """
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio payload received.",
            )

        filename = audio.filename or "speech.webm"
        logger.info(
            "[VOICE] Audio transcribe request received | filename=%s | size=%d bytes | lang=%s | session_id=%s",
            filename,
            len(audio_bytes),
            language,
            session_id,
        )

        stt_result = await hybrid_stt_provider.transcribe(
            audio_bytes=audio_bytes,
            filename=filename,
            language=language,
        )

        return TranscribeResponse(
            transcript=stt_result.transcript,
            language=stt_result.language,
            confidence=stt_result.confidence,
            provider=stt_result.provider,
            latency_ms=stt_result.latency_ms,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in /api/voice/transcribe: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio transcription failed: {str(exc)}",
        ) from exc


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

        logger.info(
            "Voice Query received | device_id=%s | lang=%s | mode=%s | text=%.60s",
            body.device_id,
            body.language,
            body.response_mode,
            query_text,
        )

        # Delegate directly to shared query service
        res = await process_user_query(
            message=query_text,
            language=body.language,
            session_id=body.session_id,
            response_mode=body.response_mode,
        )

        return VoiceQueryResponse(
            answer=res.answer,
            structured_answer=res.structured_answer,
            display_answer=res.display_answer,
            spoken_answer=res.spoken_answer,
            language=res.language,
            intent=res.intent,
            answer_focus=res.answer_focus,
            source=res.source,
            sources=res.sources,
            suggested_followups=res.suggested_followups,
            next_action=res.next_action,
            session_id=res.session_id,
            conversation_id=res.conversation_id,
            grounding_status=res.grounding_status,
            authority_level=res.authority_level,
            claims_validated=res.claims_validated,
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


class SynthesizeRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Text content to synthesize into speech audio.",
        examples=["सहकार सेतू मध्ये आपले स्वागत आहे."],
    )
    language: str = Field(
        default="mr",
        description="Target ISO language code: en | hi | mr",
    )
    gender: Optional[str] = Field(
        default="female",
        description="Voice gender preference: female | male",
    )


class SynthesizeResponse(BaseModel):
    audio_content: Optional[str] = Field(
        default=None,
        description="Base64 encoded WAV audio bytes for browser playback.",
    )
    audio_format: str = Field(default="wav", description="Audio format container.")
    language: str = Field(..., description="Language code of synthesized audio.")
    gender: str = Field(default="female", description="Voice gender used.")
    provider: str = Field(default="bhashini", description="TTS Provider used (bhashini or client_fallback).")
    success: bool = Field(default=True, description="Whether server-side TTS succeeded.")


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(body: SynthesizeRequest) -> SynthesizeResponse:
    """
    Multilingual Speech Synthesis Endpoint (TTS).

    Synthesizes text into speech audio using MeitY Bhashini TTS.
    If Bhashini TTS fails, returns success=False and audio_content=None,
    allowing the frontend to smoothly fall back to browser speechSynthesis.
    """
    clean_text = body.text.strip()
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text to synthesize cannot be empty.",
        )

    logger.info(
        "[TTS] Synthesize request received | lang=%s | gender=%s | text_len=%d",
        body.language,
        body.gender,
        len(clean_text),
    )

    if bhashini_tts_provider.is_configured:
        try:
            tts_res = await bhashini_tts_provider.generate_speech_base64(
                text=clean_text,
                language_code=body.language,
                gender=body.gender or "female",
            )
            if tts_res and tts_res.get("audio_content"):
                return SynthesizeResponse(
                    audio_content=tts_res["audio_content"],
                    audio_format=tts_res.get("audio_format", "wav"),
                    language=tts_res.get("language", body.language),
                    gender=tts_res.get("gender", body.gender or "female"),
                    provider="bhashini",
                    success=True,
                )
        except Exception as exc:
            logger.warning("[TTS] Bhashini TTS synthesis error: %s", exc)

    logger.info("[TTS] Bhashini TTS unavailable or failed -> returning fallback flag")
    return SynthesizeResponse(
        audio_content=None,
        audio_format="wav",
        language=body.language,
        gender=body.gender or "female",
        provider="client_fallback",
        success=False,
    )
