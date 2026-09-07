"""
Pydantic schemas for the /api/query endpoint.
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ── Supported languages ──────────────────────────────────────────────────────

LanguageCode = str

# ── Intent categories ─────────────────────────────────────────────────────────

IntentCode = str


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
        default="mr",
        description="ISO language code: en | hi | mr | ta | te | kn | gu | bn | pa | ml",
    )
    session_id: Optional[str] = Field(
        default=None,
        description=(
            "Existing session UUID. If null, a new session is created automatically. "
            "Pass the session_id returned from the previous response to continue a session."
        ),
    )
    response_mode: Optional[Literal["text", "voice"]] = Field(
        default="text",
        description="Response presentation mode: 'text' (detailed) or 'voice' (concise spoken answer).",
    )


# ── Response ─────────────────────────────────────────────────────────────────

class SourceItem(BaseModel):
    title: str = Field(..., description="Title of the source document.")
    source_name: Optional[str] = Field(default=None, description="Publishing organization or authority.")
    source_url: Optional[str] = Field(default=None, description="Verified official source URL if available.")
    document_id: Optional[str] = Field(default=None, description="Document UUID.")
    authority_level: Optional[str] = Field(default="OFFICIAL_GOVERNMENT", description="Authority tier: OFFICIAL_GOVERNMENT | INSTITUTIONAL | GENERAL")
    retrieved_at: Optional[str] = Field(default=None, description="ISO timestamp of retrieval.")


class SuggestedFollowup(BaseModel):
    label: str = Field(..., description="Short user-friendly suggestion text for display chip.")
    query: str = Field(..., description="Complete contextual query sent to backend when clicked.")


class AnswerSectionItem(BaseModel):
    title: Optional[str] = Field(default=None, description="Item title, step name, or key point.")
    description: Optional[str] = Field(default=None, description="Item description or procedure details.")
    name: Optional[str] = Field(default=None, description="Document name, requirement, or office name.")
    label: Optional[str] = Field(default=None, description="Fact label or stat tag (e.g. 72 HOURS).")
    value: Optional[str] = Field(default=None, description="Fact value or statutory number.")
    content: Optional[str] = Field(default=None, description="General content for single-content items.")


class AnswerSection(BaseModel):
    type: str = Field(
        ...,
        description="Section type: 'steps' | 'documents' | 'key_facts' | 'where_to_go' | 'details' | 'next_action'",
    )
    title: str = Field(..., description="Localized section title (e.g. 'What You Should Do', 'Documents You Need').")
    items: Optional[list[AnswerSectionItem]] = Field(default_factory=list, description="Structured items for list/card sections.")
    content: Optional[str] = Field(default=None, description="Text content for single-block sections.")


class StructuredAnswerPayload(BaseModel):
    direct_answer: str = Field(..., description="1-3 short, direct sentences answering the query immediately.")
    sections: list[AnswerSection] = Field(
        default_factory=list,
        description="Dynamic list of relevant structured sections decided by AI.",
    )
    spoken_answer: Optional[str] = Field(default=None, description="Short conversational spoken answer for TTS.")
    suggested_followups: list[SuggestedFollowup] = Field(
        default_factory=list,
        description="Contextual follow-up suggestions.",
    )


class QueryResponse(BaseModel):
    answer: str = Field(
        ...,
        description="The AI-generated answer.",
    )
    structured_answer: Optional[StructuredAnswerPayload] = Field(
        default=None,
        description="Dynamic structured modular answer payload for frontend card presentation.",
    )
    display_answer: Optional[str] = Field(
        default=None,
        description="Rich formatted markdown display answer for UI rendering.",
    )
    spoken_answer: Optional[str] = Field(
        default=None,
        description="Clean, natural speech plain text answer strictly optimized for TTS audio playback.",
    )
    language: LanguageCode = Field(
        ...,
        description="Language of the response.",
    )
    intent: IntentCode = Field(
        ...,
        description="Detected intent of the user's query.",
    )
    answer_focus: Optional[str] = Field(
        default="OVERVIEW",
        description="Semantic answer focus: OVERVIEW | PROCEDURE | DOCUMENTS | CONTACT | ELIGIBILITY | DEADLINE | NEXT_STEP | COMPLAINT | GENERAL",
    )
    source: Optional[str] = Field(
        default=None,
        description="Primary source document or reference.",
    )
    sources: list[SourceItem] = Field(
        default_factory=list,
        description="List of verified retrieved source citations.",
    )
    suggested_followups: list[SuggestedFollowup] = Field(
        default_factory=list,
        description="Contextual follow-up question suggestions for user to ask next.",
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
    grounding_status: Optional[str] = Field(
        default="VERIFIED",
        description="Factual grounding status: VERIFIED | PARTIALLY_VERIFIED | UNVERIFIED | REFUSED_TO_GUESS",
    )
    authority_level: Optional[str] = Field(
        default="OFFICIAL_GOVERNMENT",
        description="Overall source authority: OFFICIAL_GOVERNMENT | TRUSTED_INSTITUTION | SECONDARY | NONE",
    )
    claims_validated: bool = Field(
        default=True,
        description="Whether all factual claims in the response passed automated source validation.",
    )


# ── Chat history item ─────────────────────────────────────────────────────────

class MessageItem(BaseModel):
    role: str = Field(..., description="user | assistant")
    content: str = Field(..., description="Message text.")
    language: str = Field(..., description="Language code of the message.")
    intent: Optional[str] = Field(default=None, description="Detected intent (assistant messages only).")
