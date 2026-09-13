"""
Pydantic schemas for Phase 2C.2: Admin Operational Attention & Notifications.
All models represent strictly database-backed or real operational alerts.
"""
from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class AdminNotificationItem(BaseModel):
    id: str = Field(..., description="Deterministic unique identifier for alert deduplication")
    category: Literal["kiosks", "knowledge", "grievances", "system"] = Field(
        ..., description="Functional domain category of the alert"
    )
    severity: Literal["critical", "high", "medium", "low", "info"] = Field(
        ..., description="Controlled severity level"
    )
    title: str = Field(..., description="Short descriptive title of the alert")
    message: str = Field(..., description="Detailed operational context with entity attributes")
    entity_type: Literal["kiosk", "grievance", "knowledge_doc", "system"] = Field(
        ..., description="Underlying domain entity type"
    )
    entity_id: str = Field(..., description="Primary identifier of the underlying record")
    link_tab: Literal["kiosks", "knowledge", "grievances"] = Field(
        ..., description="Admin portal tab for deep-link resolution"
    )
    created_at: str = Field(
        ..., description="Real event/state timestamp from the underlying database record"
    )
    detected_at: str = Field(
        ..., description="Timestamp when the alert condition was detected by backend"
    )
    is_read: bool = Field(default=False, description="Read state of this alert")
    read: bool = Field(default=False, description="Alias for is_read for frontend compatibility")


class AdminNotificationListResponse(BaseModel):
    status: str = Field(default="ok", description="Status string: ok | error")
    provenance: str = Field(default="REAL_DB", description="Data provenance: REAL_DB")
    total: int = Field(..., description="Total active operational alerts count")
    unread_count: int = Field(..., description="Number of unread alerts")
    notifications: List[AdminNotificationItem] = Field(
        default_factory=list, description="List of operational alerts ordered by severity"
    )
    generated_at: str = Field(..., description="ISO 8601 UTC timestamp of alert aggregation")


class AdminNotificationReadResponse(BaseModel):
    status: str = Field(default="ok", description="Operation status")
    id: str = Field(..., description="Identifier of the marked alert")
    is_read: bool = Field(default=True, description="Updated read status")
