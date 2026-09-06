"""
Groq AI Provider for SahkaarSetu (SIH26088).

Uses Groq's high-speed inference engine (groq/compound-mini / openai/gpt-oss-20b)
for grounded multilingual query answering and live web search capabilities.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List, Tuple

from app.config import get_settings
from app.providers.ai_provider import AIProvider
from app.schemas.query import IntentCode, QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

GROQ_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

# Primary & High-Speed Fallback Groq models (official Groq model IDs)
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

_LANG_NAME = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
}


class GroqProvider(AIProvider):
    """Concrete Groq AI Provider implementation."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.groq_api_key.strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def answer_query(self, request: QueryRequest) -> QueryResponse:
        """Process query using Groq API."""
        if not self.is_configured:
            raise RuntimeError("GROQ_API_KEY is not configured in backend/.env")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SahkaarSetu-AI/1.0",
        }

        lang_name = _LANG_NAME.get(request.language, "English")
        system_prompt = (
            f"You are SahkaarSetu AI (सहकारसेतू - तुमचा सहकारी मित्र), a warm, empathetic, and trusted multilingual cooperative guide. "
            f"Please respond conversationally, helpfully, with empathy and respect in {lang_name}. Use culturally familiar honorifics (like 'शेतकरी मित्र / दादा' in Marathi or 'किसान भाई' in Hindi) and offer warm closing guidance."
        )

        user_prompt = f"Question ({lang_name}): {request.message}"

        payload = {
            "model": GROQ_MODELS[0],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 800,
        }

        answer_text = ""
        used_model = GROQ_MODELS[0]

        for model_name in GROQ_MODELS:
            payload["model"] = model_name
            req = urllib.request.Request(
                GROQ_COMPLETIONS_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        answer_text = data["choices"][0]["message"]["content"].strip()
                        used_model = model_name
                        logger.info(f"[AI PROVIDER] GROQ | [MODEL] {used_model} | [STATUS] 200 SUCCESS")
                        break
            except urllib.error.HTTPError as exc:
                logger.warning(f"[AI PROVIDER] GROQ Model '{model_name}' HTTP Error {exc.code}")
                continue
            except Exception as exc:
                logger.warning(f"[AI PROVIDER] GROQ Model '{model_name}' Exception: {exc}")
                continue

        if not answer_text:
            answer_text = "माझ्याकडे सध्या याबद्दल माहिती उपलब्ध नाही. कृपया संबंधित अधिकृत सहकार विभागाकडे संपर्क साधा."

        return QueryResponse(
            answer=answer_text,
            language=request.language,
            intent="GENERAL_COOPERATIVE",
            source="Groq AI Engine",
            next_action=None,
        )


def query_groq_llm(
    system_instruction: str,
    user_prompt: str,
    max_tokens: int = 850,
    temperature: float = 0.2,
    response_format: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[str], str, Dict[str, Any]]:
    """
    Synchronous / Thread-safe helper to query Groq LLM API with high-speed model fallback chain.
    Returns (response_text, model_used, telemetry_stats).
    """
    start_time = time.perf_counter()
    settings = get_settings()
    api_key = (settings.groq_api_key or os.getenv("GROQ_API_KEY", "")).strip()

    stats = {
        "llm_actually_called": False,
        "retries": 0,
        "timeouts": 0,
        "fallbacks": 0,
        "output_token_count": 0,
        "latency_ms": 0.0,
    }

    if not api_key:
        logger.error("[AI PROVIDER] GROQ_API_KEY missing in backend/.env")
        return None, "none", stats

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "SahkaarSetu-AI/1.0",
    }

    stats["llm_actually_called"] = True

    for idx, model_name in enumerate(GROQ_MODELS):
        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format
        req = urllib.request.Request(
            GROQ_COMPLETIONS_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["choices"][0]["message"]["content"].strip()
                    usage = data.get("usage", {})
                    stats["output_token_count"] = usage.get("completion_tokens", len(text.split()))
                    stats["latency_ms"] = (time.perf_counter() - start_time) * 1000.0
                    logger.info(f"[AI PROVIDER] GROQ | [MODEL] {model_name} | [STATUS] 200 SUCCESS ({stats['latency_ms']:.2f}ms)")
                    return text, model_name, stats
        except urllib.error.HTTPError as exc:
            stats["retries"] += 1
            if idx > 0:
                stats["fallbacks"] += 1
            err_body = exc.read().decode("utf-8", errors="ignore")[:100]
            logger.warning(f"[AI PROVIDER] GROQ Model '{model_name}' HTTP {exc.code}: {err_body}")
            continue
        except Exception as exc:
            stats["retries"] += 1
            stats["timeouts"] += 1
            if idx > 0:
                stats["fallbacks"] += 1
            logger.warning(f"[AI PROVIDER] GROQ Model '{model_name}' Exception: {exc}")
            continue

    stats["latency_ms"] = (time.perf_counter() - start_time) * 1000.0
    return None, "none", stats
