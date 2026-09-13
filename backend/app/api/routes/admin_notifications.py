"""
Admin Operational Notifications & Attention Center Router (Phase 2C.2).

Endpoints:
- GET /api/admin/notifications: Real database-backed operational alerts.
- POST /api/admin/notifications/{id}/read: Mark single alert as read.
- POST /api/admin/notifications/read-all: Mark all active alerts as read.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import require_admin_role
from app.schemas.admin_notification import (
    AdminNotificationListResponse,
    AdminNotificationReadResponse,
)
from database.repository import (
    get_admin_notifications,
    mark_admin_notification_read,
    mark_all_admin_notifications_read,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/notifications", tags=["admin-notifications"])


@router.get("", response_model=AdminNotificationListResponse)
async def list_notifications(
    current_user: dict[str, Any] = Depends(require_admin_role(["ADMIN"])),
) -> AdminNotificationListResponse:
    """
    Retrieve real database-backed operational alerts:
    - Kiosks: Offline (>15 min heartbeat) or Maintenance mode
    - Grievances: Urgent / High priority disputes or unassigned new cases
    - Knowledge: Documents with review_due, outdated, or under_review status
    - System: Actual backend degradation conditions if any
    """
    try:
        data = get_admin_notifications(user=current_user)
        return AdminNotificationListResponse(**data)
    except Exception as exc:
        logger.error("Failed to generate admin notifications: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate notifications: {str(exc)}",
        )


@router.post("/{notification_id}/read", response_model=AdminNotificationReadResponse)
async def mark_notification_read(
    notification_id: str,
    current_user: dict[str, Any] = Depends(require_admin_role(["ADMIN"])),
) -> AdminNotificationReadResponse:
    """
    Mark an operational alert as read.
    NOTE: Marking read does NOT alter the underlying database entity state.
    """
    try:
        mark_admin_notification_read(notification_id=notification_id, user=current_user)
        return AdminNotificationReadResponse(
            status="ok",
            id=notification_id,
            is_read=True,
        )
    except Exception as exc:
        logger.error("Failed to mark notification read: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification read: {str(exc)}",
        )


@router.post("/read-all")
async def mark_all_read(
    current_user: dict[str, Any] = Depends(require_admin_role(["ADMIN"])),
) -> dict[str, Any]:
    """
    Mark all currently active alerts as read.
    """
    try:
        marked = mark_all_admin_notifications_read(user=current_user)
        return {"status": "ok", "marked_count": marked}
    except Exception as exc:
        logger.error("Failed to mark all notifications read: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark all notifications read: {str(exc)}",
        )
