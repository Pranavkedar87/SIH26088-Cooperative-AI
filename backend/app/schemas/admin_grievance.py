"""
Pydantic Schemas for Admin Grievance Triage API (Phase 2A.2).
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class AdminGrievanceNoteItem(BaseModel):
    id: str = Field(..., description="Unique note identifier.")
    note: str = Field(..., description="Internal note observation text.")
    author_id: str = Field(..., description="UUID of operator who authored the note.")
    author_name: str = Field(..., description="Display name of the author.")
    author_role: str = Field(..., description="Role of the author: ADMIN | STAFF.")
    created_at: str = Field(..., description="ISO 8601 timestamp of note creation.")


class AdminGrievanceConversationMessage(BaseModel):
    role: str = Field(..., description="Message role: user | assistant.")
    content: str = Field(..., description="Message text content.")
    language: str = Field(default="en", description="Language code.")
    created_at: str = Field(..., description="ISO 8601 timestamp.")
    intent: Optional[str] = Field(default=None, description="Classified intent.")


class AdminGrievanceListItem(BaseModel):
    id: str = Field(..., description="Grievance UUID or Case ID.")
    category: str = Field(..., description="Grievance classification category.")
    description: str = Field(..., description="Citizen grievance description.")
    status: str = Field(..., description="Operational status: draft | submitted | under_review | resolved | closed.")
    priority: str = Field(default="medium", description="Priority level: urgent | high | medium | low.")
    assigned_staff: Optional[str] = Field(default=None, description="Assigned operator name or email.")
    pacs_name: Optional[str] = Field(default=None, description="Associated PACS society.")
    citizen_masked_name: str = Field(default="Citizen (Protected)", description="Masked citizen name.")
    citizen_phone_masked: str = Field(default="+91 98******45", description="Masked citizen phone number.")
    created_at: str = Field(..., description="Creation ISO timestamp.")
    updated_at: str = Field(..., description="Last update ISO timestamp.")


class AdminGrievanceListResponse(BaseModel):
    items: list[AdminGrievanceListItem] = Field(..., description="List of grievances.")
    page: int = Field(default=1, description="Current page number.")
    page_size: int = Field(default=20, description="Items per page.")
    total: int = Field(..., description="Total count matching filters.")


class AdminGrievanceDetailResponse(BaseModel):
    id: str = Field(..., description="Grievance UUID or Case ID.")
    conversation_id: Optional[str] = Field(default=None, description="Linked conversation UUID.")
    category: str = Field(..., description="Grievance classification category.")
    description: str = Field(..., description="Citizen grievance description.")
    status: str = Field(..., description="Operational status: draft | submitted | under_review | resolved | closed.")
    priority: str = Field(default="medium", description="Priority level: urgent | high | medium | low.")
    assigned_staff: Optional[str] = Field(default=None, description="Assigned operator name or email.")
    pacs_name: Optional[str] = Field(default=None, description="Associated PACS society.")
    citizen_masked_name: str = Field(default="Citizen (Protected)", description="Masked citizen name.")
    citizen_phone_masked: str = Field(default="+91 98******45", description="Masked citizen phone number.")
    ai_guidance: Optional[str] = Field(default=None, description="AI guidance provided to citizen.")
    staff_notes: list[AdminGrievanceNoteItem] = Field(default_factory=list, description="Internal verification notes.")
    conversation: list[AdminGrievanceConversationMessage] = Field(
        default_factory=list,
        description="Chronological transcript of messages from the linked citizen session.",
    )
    created_at: str = Field(..., description="Creation ISO timestamp.")
    updated_at: str = Field(..., description="Last update ISO timestamp.")


class AdminGrievanceUpdateRequest(BaseModel):
    status: Optional[str] = Field(
        default=None,
        description="Target lifecycle status: draft | submitted | under_review | resolved | closed.",
    )
    priority: Optional[str] = Field(
        default=None,
        description="Operational priority: urgent | high | medium | low.",
    )
    assigned_staff: Optional[str] = Field(
        default=None,
        description="Name or email of assigned field/desk officer.",
    )


class AdminGrievanceNoteRequest(BaseModel):
    note: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Internal verification note to append to the case history.",
    )
