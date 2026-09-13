"""
Admin Audit Logging API Route.

Provides read-only inspection of immutable administrative audit trails.
Strictly restricted to ADMIN operators. Append-only, no mutation or deletion routes exist.
"""
from __future__ import annotations

import logging
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_admin_user
from app.schemas.admin_audit import AdminAuditLogItem, AdminAuditLogListResponse
from database.repository import list_audit_logs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/audit-logs", tags=["Admin Audit Logs"])


@router.get(
    "",
    response_model=AdminAuditLogListResponse,
    summary="Query paginated administrative audit trail",
)
async def get_audit_logs_endpoint(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    action: Optional[str] = Query(default=None, description="Filter by action code, e.g. DOCUMENT_PUBLISHED"),
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type (knowledge_document, grievance, kiosk)"),
    entity_id: Optional[str] = Query(default=None, description="Filter by entity identifier"),
    user_id: Optional[str] = Query(default=None, description="Filter by operator user UUID"),
    start_date: Optional[str] = Query(default=None, description="Filter entries after this ISO 8601 timestamp"),
    end_date: Optional[str] = Query(default=None, description="Filter entries before this ISO 8601 timestamp"),
    current_user: dict[str, Any] = Depends(get_current_admin_user),
) -> AdminAuditLogListResponse:
    """
    Retrieve paginated immutable audit logs for administrative actions.
    Restricted to ADMIN operators (STAFF operators receive HTTP 403 Forbidden).
    """
    user_role = (current_user.get("role") or "").upper()
    if user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Only administrators have authority to inspect audit logs.",
        )

    try:
        result = list_audit_logs(
            page=page,
            page_size=page_size,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            user=current_user,
        )
        return AdminAuditLogListResponse(
            status="ok",
            items=[AdminAuditLogItem(**item) for item in result.get("items", [])],
            page=result.get("page", page),
            page_size=result.get("page_size", page_size),
            total=result.get("total", 0),
        )
    except Exception as exc:
        logger.error("Failed to query audit logs: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query audit logs: {str(exc)}",
        )
