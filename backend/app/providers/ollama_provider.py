"""
Ollama AI Provider for SahkaarSetu (SIH26088).

Local high-performance inference engine running via Ollama HTTP API (default: Qwen3 8B).
Architecture:
    React → FastAPI /api/query → process_user_query → RAGPipeline → OllamaProvider → local Qwen3 8B → response
"""
from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any, Optional, Tuple

from app.config import get_settings
from app.providers.ai_provider import AIProvider
from app.schemas.query import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

LOCAL_UNAVAILABLE_MESSAGE = "Local AI model is currently unavailable."


def query_ollama_llm(
    system_instruction: str,
    user_prompt: str,
    max_tokens: int = 2048,
    temperature: float = 0.2,
    response_format: Optional[str] = "json",
) -> tuple[Optional[str], str, dict[str, Any]]:
    """
    Query local Ollama instance via HTTP REST API (/api/chat).

    Returns:
        (response_text, model_used, telemetry_stats)
    """
    settings = get_settings()
    base_url = settings.ollama_base_url.rstrip("/")
    model_name = settings.ollama_model.strip()

    start_time = time.perf_counter()
    stats: dict[str, Any] = {
        "llm_actually_called": False,
        "provider": "ollama",
        "model": model_name,
        "latency_ms": 0.0,
    }

    payload: dict[str, Any] = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "keep_alive": "15m",
        "think": False,
        "options": {
            "temperature": temperature,
            "num_predict": min(max_tokens, 512),
            "num_ctx": 2048,
            "repeat_penalty": 1.15,
            "top_p": 0.9,
        },
    }

    if response_format:
        payload["format"] = response_format

    url = f"{base_url}/api/chat"
    logger.info("[AI PROVIDER] provider=ollama model=%s endpoint=%s", model_name, url)

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        stats["llm_actually_called"] = True
        with urllib.request.urlopen(req, timeout=settings.ollama_timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        dur = (time.perf_counter() - start_time) * 1000.0
        stats["latency_ms"] = dur

        message_obj = data.get("message", {})
        content = message_obj.get("content", "").strip()

        if content:
            logger.info(
                "[AI PROVIDER] provider=ollama model=%s status=SUCCESS latency=%.2fms",
                model_name,
                dur,
            )
            return content, model_name, stats

        logger.warning("[AI PROVIDER] provider=ollama model=%s returned empty content", model_name)
        return None, model_name, stats

    except urllib.error.URLError as exc:
        dur = (time.perf_counter() - start_time) * 1000.0
        stats["latency_ms"] = dur
        logger.error(
            "[AI PROVIDER] provider=ollama model=%s connection failed: %s (duration: %.2fms)",
            model_name,
            exc,
            dur,
        )
        return None, model_name, stats
    except Exception as exc:
        dur = (time.perf_counter() - start_time) * 1000.0
        stats["latency_ms"] = dur
        logger.error(
            "[AI PROVIDER] provider=ollama model=%s unexpected error: %s (duration: %.2fms)",
            model_name,
            exc,
            dur,
        )
        return None, model_name, stats


class OllamaProvider(AIProvider):
    """Concrete Ollama AI Provider implementation for local inference."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.ollama_base_url.rstrip("/")
        self.model = self.settings.ollama_model.strip()

    def check_health(self) -> dict[str, Any]:
        """
        Verify that Ollama is reachable and the configured model is installed.
        """
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                headers={"Content-Type": "application/json"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            available_models = [m.get("name") or m.get("model") for m in data.get("models", [])]
            model_installed = any(
                self.model in (m_name or "") or (m_name or "").startswith(self.model)
                for m_name in available_models
            )

            return {
                "healthy": model_installed,
                "reachable": True,
                "model": self.model,
                "available_models": available_models,
                "base_url": self.base_url,
            }
        except Exception as exc:
            logger.warning("[AI PROVIDER] Ollama health check failed: %s", exc)
            return {
                "healthy": False,
                "reachable": False,
                "model": self.model,
                "error": str(exc),
                "base_url": self.base_url,
            }

    async def answer_query(self, request: QueryRequest) -> QueryResponse:
        """
        Fallback implementation of abstract answer_query if called directly outside RAG.
        """
        system_prompt = (
            "You are SahkaarSetu AI, a helpful cooperative and agricultural guide. "
            f"Please respond in language: {request.language}."
        )
        content, used_model, _stats = query_ollama_llm(
            system_instruction=system_prompt,
            user_prompt=request.message,
            max_tokens=1000,
            temperature=0.2,
            response_format=None,
        )

        if not content:
            return QueryResponse(
                answer=LOCAL_UNAVAILABLE_MESSAGE,
                display_answer=LOCAL_UNAVAILABLE_MESSAGE,
                spoken_answer=LOCAL_UNAVAILABLE_MESSAGE,
                language=request.language,
                intent="GENERAL_COOPERATIVE",
                source="Local AI Assistant",
                sources=[],
                next_action=None,
            )

        return QueryResponse(
            answer=content,
            display_answer=content,
            spoken_answer=content,
            language=request.language,
            intent="GENERAL_COOPERATIVE",
            source="Ollama Local LLM",
            sources=[],
            next_action=None,
        )
