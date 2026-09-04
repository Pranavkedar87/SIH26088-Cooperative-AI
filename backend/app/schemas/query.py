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
    session_id: Optional[str] = Field(
        default=None,
        description=(
            "Existing session UUID. If null, a new session is created automatically. "
            "Pass the session_id returned from the previous response to continue a session."
        ),
    )


# ── Response ─────────────────────────────────────────────────────────────────

class SourceItem(BaseModel):
    title: str = Field(..., description="Title of the source document.")
    source_name: Optional[str] = Field(default=None, description="Publishing organization or authority.")
    source_url: Optional[str] = Field(default=None, description="Verified official source URL if available.")
    document_id: Optional[str] = Field(default=None, description="Document UUID.")


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
        description="Primary source document or reference.",
    )
    sources: list[SourceItem] = Field(
        default_factory=list,
        description="List of verified retrieved source citations.",
    )
    next_action: Optional[str] = Field(
        default=None,
        description="Suggested follow-up action.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session UUID — pass this back with subsequent requests to maintain context.",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation UUID — use this to fetch chat history via GET /api/conversations/{id}/messages.",
    )


# ── Chat history item ─────────────────────────────────────────────────────────

class MessageItem(BaseModel):
    role: str = Field(..., description="user | assistant")
    content: str = Field(..., description="Message text.")
    language: str = Field(..., description="Language code of the message.")
    intent: Optional[str] = Field(default=None, description="Detected intent (assistant messages only).")
