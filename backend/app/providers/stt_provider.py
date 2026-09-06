"""
Abstract STT Provider Interface and Groq Whisper Implementation for SahkaarSetu.

Supports reliable server-side audio transcription for English, Hindi, Marathi,
and other Indian languages without depending on browser SpeechRecognition.
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)

GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

# Standard ISO language code mapping for STT providers
STT_LANG_MAPPING: Dict[str, str] = {
    "en": "en",
    "hi": "hi",
    "mr": "mr",
    "ta": "ta",
    "te": "te",
    "kn": "kn",
    "gu": "gu",
    "bn": "bn",
    "pa": "pa",
    "ml": "ml",
    "en-IN": "en",
    "hi-IN": "hi",
    "mr-IN": "mr",
}

STT_MODELS = [
    "whisper-large-v3-turbo",
    "whisper-large-v3",
]


class STTResult:
    def __init__(
        self,
        transcript: str,
        language: str,
        confidence: float = 0.95,
        provider: str = "groq_whisper",
        latency_ms: float = 0.0,
    ):
        self.transcript = transcript
        self.language = language
        self.confidence = confidence
        self.provider = provider
        self.latency_ms = latency_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transcript": self.transcript,
            "language": self.language,
            "confidence": self.confidence,
            "provider": self.provider,
            "latency_ms": round(self.latency_ms, 2),
        }


class STTProvider(ABC):
    """Abstract base class for speech-to-text providers."""

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "speech.webm",
        language: str = "mr",
    ) -> STTResult:
        """
        Transcribe raw audio bytes into text in the specified language.
        """
        ...


class GroqWhisperProvider(STTProvider):
    """Concrete Groq Whisper STT implementation."""

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = (api_key or settings.groq_api_key or "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "speech.webm",
        language: str = "mr",
    ) -> STTResult:
        start_time = time.perf_counter()
        if not self.is_configured:
            raise RuntimeError("GROQ_API_KEY is not configured in backend/.env for STT provider")

        mapped_lang = STT_LANG_MAPPING.get(language, language.split("-")[0] if "-" in language else language)

        # Detect content type from filename extension
        content_type = "audio/webm"
        if filename.endswith(".mp4") or filename.endswith(".m4a"):
            content_type = "audio/mp4"
        elif filename.endswith(".wav"):
            content_type = "audio/wav"
        elif filename.endswith(".ogg"):
            content_type = "audio/ogg"
        elif filename.endswith(".mp3"):
            content_type = "audio/mpeg"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        last_exception = None

        for model_name in STT_MODELS:
            try:
                files = {
                    "file": (filename, audio_bytes, content_type),
                }
                data = {
                    "model": model_name,
                    "language": mapped_lang,
                    "response_format": "json",
                    "temperature": "0.0",
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        GROQ_STT_URL,
                        headers=headers,
                        data=data,
                        files=files,
                    )

                if resp.status_code == 200:
                    resp_data = resp.json()
                    transcript = resp_data.get("text", "").strip()
                    latency_ms = (time.perf_counter() - start_time) * 1000.0

                    logger.info(
                        "[STT] Groq Whisper success | model=%s | lang=%s | size=%d bytes | latency=%.2fms | transcript='%.60s'",
                        model_name,
                        mapped_lang,
                        len(audio_bytes),
                        latency_ms,
                        transcript,
                    )

                    return STTResult(
                        transcript=transcript,
                        language=mapped_lang,
                        confidence=0.98,
                        provider="groq_whisper",
                        latency_ms=latency_ms,
                    )
                else:
                    logger.warning(
                        "[STT] Groq Whisper model %s HTTP %d: %s",
                        model_name,
                        resp.status_code,
                        resp.text[:100],
                    )

            except Exception as exc:
                logger.warning("[STT] Groq Whisper model %s error: %s", model_name, exc)
                last_exception = exc

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        raise RuntimeError(f"All Groq Whisper STT models failed: {last_exception}")


class BhashiniProvider(STTProvider):
    """Optional Bhashini STT Provider (Extensible placeholder)."""

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "speech.webm",
        language: str = "mr",
    ) -> STTResult:
        raise NotImplementedError("Bhashini STT provider is not enabled.")


class BrowserSpeechProvider(STTProvider):
    """Optional Browser Speech STT Provider (Fallback metadata holder)."""

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "speech.webm",
        language: str = "mr",
    ) -> STTResult:
        raise NotImplementedError("BrowserSpeechProvider runs client-side.")
