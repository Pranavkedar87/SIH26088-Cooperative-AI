"""
Pydantic schemas for the /api/query endpoint.
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ── Supported languages ──────────────────────────────────────────────────────

LanguageCode = Literal["en", "hi", "mr"]

# ── Intent categories ─────────────────────────────────────────────────────────

IntentCode = Literal[
    "COOPERATIVE_LAW",
    "COOPERATIVE_BYLAW",
    "MINISTRY_SCHEME",
    "PACS_SERVICE",
    "PMFBY",
    "AGRICULTURAL_SUPPORT",
    "FINANCIAL_LITERACY",
    "GRIEVANCE",
    "GENERAL_COOPERATIVE",
]


# ── Request ──────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's question or message.",
        examples=["What are the rules for PACS registration?"],
    )
    language: LanguageCode = Field(
        default="en",
        description="ISO 639-1 language code for the response.",
    )


# ── Response ─────────────────────────────────────────────────────────────────

class QueryResponse(BaseModel):
    answer: str = Field(
        ...,
        description="The AI-generated answer.",
    )
    language: LanguageCode = Field(
        ...,
        description="Language of the response.",
    )
    intent: IntentCode = Field(
        ...,
        description="Detected intent of the user's query.",
    )
    source: Optional[str] = Field(
        default=None,
        description="Source document or reference (populated in RAG milestone).",
    )
    next_action: Optional[str] = Field(
        default=None,
        description="Suggested follow-up action (populated in grievance/workflow milestone).",
    )
