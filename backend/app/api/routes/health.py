"""
Health check endpoint.

GET /health → {"status": "ok"}

Used by Render, load balancers, and the frontend to verify the backend is alive.
"""
from typing import Any
from fastapi import APIRouter
from app.config import get_settings
from app.providers.ollama_provider import OllamaProvider

router = APIRouter(tags=["health"])


@router.get("/")
@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Return a liveness signal and AI provider health status."""
    settings = get_settings()
    provider_name = (settings.ai_provider or "ollama").lower().strip()

    provider_health = None
    if provider_name == "ollama":
        ollama_prov = OllamaProvider()
        provider_health = ollama_prov.check_health()

    return {
        "status": "ok",
        "service": "Sahakari AI Sahayak API",
        "ai_provider": provider_name,
        "model": settings.ollama_model if provider_name == "ollama" else "gemini-2.5-flash",
        "provider_health": provider_health,
        "docs": "/docs",
        "health": "/health",
    }

