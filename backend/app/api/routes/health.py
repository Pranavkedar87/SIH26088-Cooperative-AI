"""
Health check endpoint.

GET /health → {"status": "ok"}

Used by Render, load balancers, and the frontend to verify the backend is alive.
"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return a simple liveness signal."""
    return {
        "status": "ok",
        "service": "Sahakari AI Sahayak API",
        "docs": "/docs",
        "health": "/health",
    }

