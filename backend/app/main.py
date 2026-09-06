"""
FastAPI application entry point.

Startup order:
  1. Load settings (from .env)
  2. Configure logging
  3. Register CORS middleware
  4. Mount routers
"""
from __future__ import annotations
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.routes import health, query, conversations, voice, vision, knowledge, grievance

# ── Settings ─────────────────────────────────────────────────────────────────
settings = get_settings()

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Cooperative AI Assistant API",
    description=(
        "Backend for SIH26088 — Multilingual Cooperative Governance "
        "& Legal Assistance Chatbot."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(query.router)
app.include_router(conversations.router)
app.include_router(voice.router)
app.include_router(vision.router)
app.include_router(knowledge.router)
app.include_router(grievance.router)

logger.info("Cooperative AI Assistant API started | env=%s", settings.app_env)

