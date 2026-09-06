"""
Bhashini Multilingual Speech & Language API Provider for SahkaarSetu (SIH26088).

Integrates with MeitY Bhashini ULCA Pipeline Inference endpoints for:
1. Speech-to-Text (ASR) in Marathi (mr), Hindi (hi), and English (en)
2. Text-to-Speech (TTS) in Marathi (mr), Hindi (hi), and English (en)
"""
from __future__ import annotations

import logging
import httpx
from typing import Optional, Dict, Any
from app.config import get_settings

logger = logging.getLogger(__name__)

BHASHINI_PIPELINE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"


class BhashiniProvider:
    """Interface for official MeitY Bhashini Multilingual Speech API."""

    def __init__(self):
        settings = get_settings()
        self.user_id = settings.bhashini_user_id.strip()
        self.api_key = settings.bhashini_api_key.strip()
        self.pipeline_id = settings.bhashini_pipeline_id.strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.user_id and self.api_key)

    async def transcribe_audio_base64(self, audio_base64: str, language_code: str = "mr") -> Optional[str]:
        """
        Converts base64 audio to text using Bhashini ASR pipeline.
        Supported languages: mr (Marathi), hi (Hindi), en (English)
        """
        if not self.is_configured:
            logger.warning("[BHASHINI] API credentials not configured in backend/.env")
            return None

        headers = {
            "Content-Type": "application/json",
            "userID": self.user_id,
            "ulcaApiKey": self.api_key,
        }

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {"sourceLanguage": language_code},
                        "serviceId": "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4",
                        "audioFormat": "wav",
                        "samplingRate": 16000,
                    },
                }
            ],
            "inputData": {
                "audio": [
                    {
                        "audioContent": audio_base64,
                    }
                ]
            },
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(BHASHINI_PIPELINE_URL, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    transcript = data["pipelineResponse"][0]["output"][0]["source"]
                    logger.info(f"[BHASHINI_ASR] Success ({language_code}): {transcript}")
                    return transcript
                else:
                    logger.error(f"[BHASHINI_ASR] Failed with status {response.status_code}: {response.text}")
                    return None
        except Exception as exc:
            logger.error(f"[BHASHINI_ASR] Exception during request: {exc}")
            return None

    async def generate_speech_base64(self, text: str, language_code: str = "mr", gender: str = "female") -> Optional[str]:
        """
        Converts text to speech base64 audio using Bhashini TTS pipeline.
        """
        if not self.is_configured:
            logger.warning("[BHASHINI] API credentials not configured in backend/.env")
            return None

        headers = {
            "Content-Type": "application/json",
            "userID": self.user_id,
            "ulcaApiKey": self.api_key,
        }

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "tts",
                    "config": {
                        "language": {"sourceLanguage": language_code},
                        "serviceId": f"ai4bharat/indic-tts-coqui-multilingual-{gender}",
                        "gender": gender,
                    },
                }
            ],
            "inputData": {
                "input": [
                    {
                        "source": text,
                    }
                ]
            },
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(BHASHINI_PIPELINE_URL, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    audio_b64 = data["pipelineResponse"][0]["audio"][0]["audioContent"]
                    logger.info(f"[BHASHINI_TTS] Success ({language_code})")
                    return audio_b64
                else:
                    logger.error(f"[BHASHINI_TTS] Failed with status {response.status_code}: {response.text}")
                    return None
        except Exception as exc:
            logger.error(f"[BHASHINI_TTS] Exception during request: {exc}")
            return None
