"""
Pydantic schemas for the /api/vision/analyze document scanning endpoint.
"""
from __future__ import annotations
from typing import Literal, Optional, Dict, List, Any
from pydantic import BaseModel, Field

# ── Controlled Document Types ──────────────────────────────────────────────────
DocumentType = Literal[
    "PMFBY_POLICY",
    "LAND_RECORD_7_12",
    "COOPERATIVE_NOTICE",
    "PACS_MEMBERSHIP_FORM",
    "SUBSIDY_LETTER",
    "FERTILIZER_RECEIPT",
    "LOAN_PASSBOOK",
    "IDENTITY_DOCUMENT",
    "UNKNOWN",
]

# ── Controlled Readability Statuses ────────────────────────────────────────────
ReadabilityStatus = Literal[
    "CLEAR",
    "BLURRY",
    "CROPPED",
    "POOR_LIGHTING",
]


class VisionAnalyzeResponse(BaseModel):
    """
    Response schema for POST /api/vision/analyze.
    """
    success: bool = Field(
        ...,
        description="Whether the document was successfully processed and analyzed.",
    )
    document_type: DocumentType = Field(
        default="UNKNOWN",
        description="Classified cooperative/agricultural document type.",
    )
    readability: ReadabilityStatus = Field(
        default="CLEAR",
        description="Visual clarity and readability assessment of the document.",
    )
    detected_language: str = Field(
        default="unknown",
        description="Primary language detected in the document (e.g. 'mr', 'hi', 'en').",
    )
    key_fields: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Extracted key-value pairs (with sensitive PII masked).",
    )
    document_summary: Optional[str] = Field(
        default=None,
        description="2-3 sentence plain-language summary of the document.",
    )
    suggested_questions: List[str] = Field(
        default_factory=list,
        description="Relevant follow-up questions a citizen might ask about this document.",
    )
    has_sensitive_pii: bool = Field(
        default=False,
        description="Whether sensitive PII (Aadhaar, PAN, bank account, mobile) was detected.",
    )
    refusal_reason: Optional[str] = Field(
        default=None,
        description="Safe explanation if analysis was refused (e.g. for identity cards).",
    )
    processing_time_ms: Optional[float] = Field(
        default=None,
        description="End-to-end vision processing latency in milliseconds.",
    )
