"""
Pydantic Schemas for Citizen Human Handoff / "Get Help from PACS" (Phase 3A.1).
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class HandoffCreateRequest(BaseModel):
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation UUID associated with this assistance handoff.",
    )
    language: str = Field(
        default="mr",
        description="Original language used by the citizen: mr | hi | en.",
    )
    target_officer_language: Optional[str] = Field(
        default="en",
        description="Preferred language for officer slip notes: en | hi | mr.",
    )
    citizen_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional citizen or member name.",
    )
    citizen_phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional contact number.",
    )
    pacs_name: Optional[str] = Field(
        default=None,
        max_length=250,
        description="Name of the PACS society or local cooperative organization.",
    )
    village: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional village or taluka name.",
    )
    category: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Grievance or assistance category: PMFBY | PACS_SERVICE | COOPERATIVE_LAW | etc.",
    )
    description: str = Field(
        ...,
        min_length=5,
        max_length=4000,
        description="Original citizen question, grievance, or assistance issue.",
    )
    ai_guidance: Optional[str] = Field(
        default=None,
        description="Grounded AI guidance previously presented to citizen.",
    )
    source_citations: Optional[list[Any]] = Field(
        default_factory=list,
        description="List of verified legal, scheme, or PACS sources cited.",
    )
    priority: Optional[str] = Field(
        default="medium",
        description="Assistance priority level: urgent | high | medium | low.",
    )


class AssistanceSlipData(BaseModel):
    header: str = Field(default="SAHKAARSETU PACS ASSISTANCE REFERENCE SLIP")
    reference_code: str
    created_at: str
    pacs_name: str
    village: Optional[str] = None
    category: str
    citizen_masked_name: str
    citizen_phone_masked: str
    citizen_language: str
    officer_language: str
    original_query: str
    officer_translated_note: str
    ai_guidance_summary: str
    sources: list[str] = Field(default_factory=list)
    qr_payload: str
    disclaimer: str


class HandoffResponse(BaseModel):
    success: bool = Field(default=True, description="Whether handoff creation was successful.")
    grievance_id: str = Field(..., description="Database UUID for the handoff record.")
    reference_code: str = Field(..., description="Human-readable reference code: PACS-2026-XXXXXX.")
    category: str = Field(..., description="Issue classification category.")
    pacs_name: Optional[str] = Field(default=None, description="Target PACS society.")
    village: Optional[str] = Field(default=None, description="Target village if provided.")
    citizen_masked_name: str = Field(..., description="Masked citizen name for privacy.")
    citizen_phone_masked: str = Field(..., description="Masked citizen contact for privacy.")
    citizen_language: str = Field(..., description="Original citizen language code.")
    officer_language: str = Field(..., description="Officer note language code.")
    original_description: str = Field(..., description="Original citizen query text.")
    translated_summary: Optional[str] = Field(default=None, description="Translated summary for officer triage.")
    translation_status: str = Field(
        ...,
        description="Status of translation: translated | untranslated_fallback | same_language",
    )
    ai_guidance: Optional[str] = Field(default=None, description="Preserved AI guidance summary.")
    source_citations: list[Any] = Field(default_factory=list, description="Verified sources cited.")
    slip_data: AssistanceSlipData = Field(..., description="Structured data formatted for 58mm assistance slip.")
    disclaimer: str = Field(..., description="Statutory facilitation disclaimer.")
    created_at: str = Field(..., description="ISO 8601 timestamp of creation.")
