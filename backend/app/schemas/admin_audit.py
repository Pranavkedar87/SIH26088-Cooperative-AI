"""
Admin Audit Logging Pydantic Schemas.

Covers append-only immutable operational audit trails for administrative actions
(knowledge verification/publishing/reindexing, grievance triage, kiosk configuration).
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class AdminAuditLogItem(BaseModel):
    id: str = Field(..., description="Unique UUID of the audit log entry")
    user_id: Optional[str] = Field(None, description="UUID of the operator who performed the action")
    user_name: str = Field(..., description="Display name or email of the operator")
    user_role: str = Field(..., description="Role of the operator: ADMIN or STAFF")
    action: str = Field(..., description="Operational action key, e.g. DOCUMENT_PUBLISHED")
    entity_type: str = Field(..., description="Domain entity type: knowledge_document, grievance, kiosk")
    entity_id: str = Field(..., description="Unique identifier of the affected entity")
    details: Optional[dict[str, Any]] = Field(default=None, description="Sanitized, non-sensitive audit details")
    created_at: str = Field(..., description="ISO 8601 UTC timestamp of the action")


class AdminAuditLogListResponse(BaseModel):
    status: str = Field("ok", description="Response status")
    items: list[AdminAuditLogItem] = Field(default_factory=list, description="Paginated list of audit records")
    page: int = Field(1, description="Current page number (1-indexed)")
    page_size: int = Field(20, description="Page size limit")
    total: int = Field(0, description="Total matching audit records count")
