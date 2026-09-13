"""
Bhashini Multilingual Speech & Language API Provider for SahkaarSetu (SIH26088).

Integrates with official MeitY Bhashini Dhruva Pipeline Inference API for:
1. Speech-to-Text (ASR) in English (en), Hindi (hi), and Marathi (mr)
2. Text-to-Speech (TTS) in English (en), Hindi (hi), and Marathi (mr)
3. Neural Machine Translation (NMT) across scheduled Indian languages
"""
from __future__ import annotations

import logging
import httpx
from typing import Optional, Dict, Any
from app.config import get_settings

logger = logging.getLogger(__name__)

BHASHINI_PIPELINE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

BHASHINI_LANG_MAP: Dict[str, str] = {
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
    "or": "or",
    "as": "as",
    "ur": "ur",
    "sa": "sa",
    "ks": "ks",
    "ne": "ne",
    "sd": "sd",
    "en-IN": "en",
    "hi-IN": "hi",
    "mr-IN": "mr",
}


class BhashiniProvider:
    """Interface for official MeitY Bhashini Multilingual Speech & Language API."""

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = (api_key or settings.bhashini_api_key or "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": self.api_key,
        }

    async def transcribe_audio_base64(
        self, audio_base64: str, language_code: str = "mr"
    ) -> Optional[str]:
        """
        Converts base64 audio to text using Bhashini ASR pipeline.
        Supported validated languages: en (English), hi (Hindi), mr (Marathi).
        """
        if not self.is_configured:
            logger.warning("[BHASHINI] API key not configured in backend/.env")
            return None

        if not audio_base64 or not audio_base64.strip():
            logger.warning("[BHASHINI_ASR] Empty audio payload provided.")
            return None

        mapped_lang = BHASHINI_LANG_MAP.get(
            language_code, language_code.split("-")[0] if "-" in language_code else language_code
        )

        headers = self._get_headers()
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {"sourceLanguage": mapped_lang},
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
                    pipeline_resp = data.get("pipelineResponse", [])
                    if pipeline_resp and "output" in pipeline_resp[0]:
                        outputs = pipeline_resp[0]["output"]
                        if outputs and "source" in outputs[0]:
                            transcript = outputs[0]["source"].strip()
                            logger.info(
                                "[BHASHINI_ASR] Success | lang=%s | transcript='%.60s'",
                                mapped_lang,
                                transcript,
                            )
                            return transcript
                    logger.warning("[BHASHINI_ASR] 200 OK but missing expected output structure")
                    return None
                else:
                    logger.warning(
                        "[BHASHINI_ASR] Failed with HTTP %d: %.100s",
                        response.status_code,
                        response.text,
                    )
                    return None
        except Exception as exc:
            logger.warning("[BHASHINI_ASR] Exception during request: %s", exc)
            return None

    async def generate_speech_base64(
        self, text: str, language_code: str = "mr", gender: str = "female"
    ) -> Optional[Dict[str, Any]]:
        """
        Converts text to speech base64 audio using Bhashini TTS pipeline.
        Returns a dict with {"audio_content": base64_str, "audio_format": "wav"}.
        """
        if not self.is_configured:
            logger.warning("[BHASHINI] API key not configured in backend/.env")
            return None

        if not text or not text.strip():
            logger.warning("[BHASHINI_TTS] Empty text provided for synthesis.")
            return None

        mapped_lang = BHASHINI_LANG_MAP.get(
            language_code, language_code.split("-")[0] if "-" in language_code else language_code
        )

        headers = self._get_headers()

        # Try specified gender first
        genders_to_try = [gender]
        if mapped_lang == "mr" and gender == "female":
            # For Marathi, male voice has higher stability/availability
            genders_to_try.append("male")
        elif gender == "female":
            genders_to_try.append("male")

        for try_gender in genders_to_try:
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "tts",
                        "config": {
                            "language": {"sourceLanguage": mapped_lang},
                            "gender": try_gender,
                        },
                    }
                ],
                "inputData": {
                    "input": [
                        {
                            "source": text[:800],  # Keep within synthesis limits for optimal latency
                        }
                    ]
                },
            }

            try:
                async with httpx.AsyncClient(timeout=12.0) as client:
                    response = await client.post(BHASHINI_PIPELINE_URL, headers=headers, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        pipeline_resp = data.get("pipelineResponse", [])
                        if pipeline_resp and "audio" in pipeline_resp[0]:
                            audios = pipeline_resp[0]["audio"]
                            if audios and "audioContent" in audios[0]:
                                audio_b64 = audios[0]["audioContent"]
                                audio_fmt = (
                                    pipeline_resp[0].get("config", {}).get("audioFormat", "wav")
                                )
                                logger.info(
                                    "[BHASHINI_TTS] Success | lang=%s | gender=%s | size=%d chars",
                                    mapped_lang,
                                    try_gender,
                                    len(audio_b64),
                                )
                                return {
                                    "audio_content": audio_b64,
                                    "audio_format": audio_fmt,
                                    "language": mapped_lang,
                                    "gender": try_gender,
                                }
                    else:
                        logger.warning(
                            "[BHASHINI_TTS] HTTP %d (lang=%s, gender=%s): %.100s",
                            response.status_code,
                            mapped_lang,
                            try_gender,
                            response.text,
                        )
            except Exception as exc:
                logger.warning(
                    "[BHASHINI_TTS] Exception (lang=%s, gender=%s): %s",
                    mapped_lang,
                    try_gender,
                    exc,
                )

        return None

    async def translate_text(
        self, text: str, source_lang: str = "en", target_lang: str = "mr"
    ) -> Optional[str]:
        """
        Translates text between Indian languages using Bhashini NMT pipeline.
        """
        if not self.is_configured:
            return None

        src_mapped = BHASHINI_LANG_MAP.get(source_lang, source_lang)
        tgt_mapped = BHASHINI_LANG_MAP.get(target_lang, target_lang)

        headers = self._get_headers()
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": src_mapped,
                            "targetLanguage": tgt_mapped,
                        }
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
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(BHASHINI_PIPELINE_URL, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    pipeline_resp = data.get("pipelineResponse", [])
                    if pipeline_resp and "output" in pipeline_resp[0]:
                        outputs = pipeline_resp[0]["output"]
                        if outputs and "target" in outputs[0]:
                            return outputs[0]["target"].strip()
                return None
        except Exception as exc:
            logger.warning("[BHASHINI_NMT] Exception: %s", exc)
            return None
