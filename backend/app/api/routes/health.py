"""
Health check endpoint.

GET /health → {"status": "ok"}

Used by Render, load balancers, and the frontend to verify the backend is alive.
"""
from typing import Any
from fastapi import APIRouter
from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/")
@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Return lightweight liveness and system configuration status."""
    settings = get_settings()
    return {
        "status": "ok",
        "service": "Sahakari AI Sahayak API",
        "ai_provider": "gemini",
        "model": "gemini-2.5-flash",
        "embedding_provider": "gemini",
        "embedding_model": "gemini-embedding-001",
        "docs": "/docs",
        "health": "/health",
    }
