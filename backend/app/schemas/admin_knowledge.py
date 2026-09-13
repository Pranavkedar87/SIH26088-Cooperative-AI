"""
Pydantic schemas for Phase 2B.2: Admin Knowledge Document Ingestion & Review.
"""
from __future__ import annotations

from typing import Optional, List, Union
from pydantic import BaseModel, Field


class AdminKnowledgeDocumentResponse(BaseModel):
    id: str = Field(..., description="Unique document UUID")
    title: str = Field(..., description="Document title")
    description: Optional[str] = Field(None, description="Document description or summary")
    source_name: Optional[str] = Field(None, description="Publishing authority or source entity")
    source_url: Optional[str] = Field(None, description="Official online source link")
    document_type: str = Field(default="GUIDELINE", description="Document taxonomy category")
    language: str = Field(default="en", description="Language: en, mr, hi")
    status: str = Field(default="draft", description="Governance lifecycle status: draft | under_review | verified | published")
    version: str = Field(default="v1.0", description="Document version string")
    is_current: bool = Field(default=False, description="Flag indicating whether document is current in force")
    authority_level: Optional[str] = Field(default="UNKNOWN", description="Authority tier: CENTRAL_GOVERNMENT, STATE_GOVERNMENT, etc.")
    jurisdiction: Optional[str] = Field(default="MAHARASHTRA", description="Legal jurisdiction")
    applicability: List[str] = Field(default_factory=lambda: ["ALL_COOPERATIVES"], description="Target societies / schemes")
    year: Optional[int] = Field(None, description="Promulgation year")
    effective_date: Optional[str] = Field(None, description="Statutory effective date (YYYY-MM-DD)")
    expiry_review_date: Optional[str] = Field(None, description="Review due or expiration date (YYYY-MM-DD)")
    verification_status: str = Field(default="NEEDS_VERIFICATION", description="Conservative verification state")
    currentness_status: str = Field(default="NEEDS_VERIFICATION", description="Conservative currency state")
    precedence_tier: int = Field(default=50, description="Legal hierarchy precedence tier (10-100)")
    raw_file_url: Optional[str] = Field(None, description="Download or reference URL for the uploaded file")
    storage_path: Optional[str] = Field(None, description="Internal storage identifier")
    file_name: Optional[str] = Field(None, description="Sanitized original filename")
    file_size_bytes: Optional[int] = Field(None, description="Uploaded file size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME content type")
    review_notes: Optional[str] = Field(None, description="Administrative or triage notes")
    created_by: Optional[str] = Field(None, description="Operator user ID who initiated upload")
    created_at: Optional[str] = Field(None, description="Timestamp of document creation")
    updated_at: Optional[str] = Field(None, description="Timestamp of last update")


class AdminKnowledgeListResponse(BaseModel):
    items: List[AdminKnowledgeDocumentResponse] = Field(..., description="Paginated knowledge document list")
    total: int = Field(..., description="Total records matching filters")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Number of items per page")
    total_pages: int = Field(default=1, description="Total pages available")


class AdminKnowledgeReviewTransitionRequest(BaseModel):
    notes: Optional[str] = Field(None, max_length=1000, description="Optional reviewer or submission notes")


class AdminKnowledgeVerifyRequest(BaseModel):
    verification_notes: Optional[str] = Field(None, max_length=1000, description="Legal verification and compliance notes")
    authority: Optional[str] = Field(None, description="Verified issuing authority")
    authority_level: Optional[str] = Field(None, description="Verified issuing authority level")
    jurisdiction: Optional[str] = Field(None, description="Verified statutory jurisdiction")
    applicability: Optional[Union[List[str], str]] = Field(None, description="Verified applicability societies or schemes")
    effective_date: Optional[str] = Field(None, description="Verified statutory effective date (YYYY-MM-DD)")
    expiry_review_date: Optional[str] = Field(None, description="Verified sunset or review expiry date (YYYY-MM-DD)")
    precedence_tier: Optional[int] = Field(None, ge=1, le=100, description="Verified legal precedence tier (1-100)")


class AdminKnowledgePublishRequest(BaseModel):
    notes: Optional[str] = Field(None, max_length=1000, description="Optional publication rationale or release notes")


class AdminKnowledgeStatusResponse(BaseModel):
    status: str = Field(..., description="Operation status: ok | error")
    message: str = Field(..., description="Descriptive status message")
    document: AdminKnowledgeDocumentResponse = Field(..., description="Updated document record")


class AdminKnowledgePublishResponse(BaseModel):
    status: str = Field(default="ok", description="Operation status: ok | error")
    message: str = Field(..., description="Descriptive status message")
    published_chunks_count: int = Field(..., description="Total vector chunks generated and stored")
    embedding_model: str = Field(default="gemini-embedding-001", description="Gemini embedding model used")
    vector_dimension: int = Field(default=768, description="Vector embedding dimension (768)")
    document: AdminKnowledgeDocumentResponse = Field(..., description="Published document record")


class AdminKnowledgeVersionItem(BaseModel):
    id: str = Field(..., description="Document UUID")
    document_id: str = Field(..., description="Document ID")
    version: str = Field(..., description="Version label e.g. v1.0, v2.0")
    status: str = Field(..., description="Lifecycle status e.g. published, draft, superseded")
    is_current: bool = Field(..., description="Whether this version is current in force")
    effective_date: Optional[str] = Field(None, description="Statutory effective date")
    verification_status: Optional[str] = Field(None, description="Verification status")
    currentness_status: Optional[str] = Field(None, description="Currentness status")
    published_at: Optional[str] = Field(None, description="Timestamp of publication")
    reviewed_at: Optional[str] = Field(None, description="Timestamp of review/verification")
    superseded_by: Optional[str] = Field(None, description="ID or version of superseding document if any")
    created_at: Optional[str] = Field(None, description="Timestamp of creation")
    updated_at: Optional[str] = Field(None, description="Timestamp of last update")
    created_by: Optional[str] = Field(None, description="Operator user who created")
    published_by: Optional[str] = Field(None, description="Admin user who published")
    chunks_count: Optional[int] = Field(default=0, description="Number of vector chunks currently active for this document")


class AdminKnowledgeVersionHistoryResponse(BaseModel):
    status: str = Field(default="ok", description="Operation status: ok | error")
    document_id: str = Field(..., description="Requested document ID")
    lineage_title: str = Field(..., description="Title identifying the document lineage")
    current_version: Optional[str] = Field(None, description="Version string of current in-force document")
    total_versions: int = Field(..., description="Total version records in this lineage")
    versions: List[AdminKnowledgeVersionItem] = Field(..., description="List of versions ordered chronologically")


class AdminKnowledgeReindexRequest(BaseModel):
    notes: Optional[str] = Field(None, max_length=1000, description="Optional re-indexing rationale or audit note")


class AdminKnowledgeReindexResponse(BaseModel):
    status: str = Field(default="ok", description="Operation status: ok | error")
    message: str = Field(..., description="Descriptive status message")
    document_id: str = Field(..., description="Document UUID")
    version: str = Field(..., description="Document version string")
    document_status: str = Field(default="published", description="Document lifecycle status")
    is_current: bool = Field(default=True, description="Whether document is currently active")
    chunks_created: int = Field(..., description="Total fresh vector chunks generated and stored")
    embedding_model: str = Field(default="gemini-embedding-001", description="Gemini embedding model used")
    embedding_dimension: int = Field(default=768, description="Vector embedding dimension (768)")
    reindexed_at: str = Field(..., description="Timestamp of re-indexing completion")


