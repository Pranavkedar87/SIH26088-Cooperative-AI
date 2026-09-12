"""
Admin Grievance Triage & Redressal Endpoints (Phase 2A.2).

GET /api/admin/grievances
  → List grievances with pagination, filtering, search, and RBAC isolation.

GET /api/admin/grievances/{id}
  → Detailed case view with citizen conversation transcript and masked PII.

PATCH /api/admin/grievances/{id}
  → Controlled updates (status transition, priority, staff assignment).

POST /api/admin/grievances/{id}/notes
  → Append internal operational/investigation note.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_admin_user
from app.schemas.admin_grievance import (
    AdminGrievanceDetailResponse,
    AdminGrievanceListResponse,
    AdminGrievanceNoteRequest,
    AdminGrievanceUpdateRequest,
)
from database.repository import (
    append_grievance_note,
    get_admin_grievance_by_id,
    list_admin_grievances,
    update_admin_grievance,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/grievances", tags=["admin-grievances"])


@router.get("", response_model=AdminGrievanceListResponse)
async def list_grievances(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Status filter"),
    priority_filter: Optional[str] = Query(default=None, alias="priority", description="Priority filter"),
    category_filter: Optional[str] = Query(default=None, alias="category", description="Category filter"),
    pacs_filter: Optional[str] = Query(default=None, alias="pacs", description="PACS name filter"),
    search: Optional[str] = Query(default=None, description="Free-text search"),
    current_user: dict[str, Any] = Depends(get_current_admin_user),
) -> AdminGrievanceListResponse:
    """
    List operational grievances with RBAC:
    - ADMIN: Sees all cases across all PACS.
    - STAFF: Only sees cases assigned to them or in their PACS society.
    """
    res = list_admin_grievances(
        page=page,
        page_size=page_size,
        status=status_filter,
        priority=priority_filter,
        category=category_filter,
        pacs=pacs_filter,
        search=search,
        user=current_user,
    )
    return AdminGrievanceListResponse(**res)


@router.get("/{grievance_id}", response_model=AdminGrievanceDetailResponse)
async def get_grievance_detail(
    grievance_id: str,
    current_user: dict[str, Any] = Depends(get_current_admin_user),
) -> AdminGrievanceDetailResponse:
    """
    Retrieve single grievance detail with conversation history and RBAC check.
    """
    try:
        record = get_admin_grievance_by_id(grievance_id, current_user)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance case '{grievance_id}' was not found.",
        )

    return AdminGrievanceDetailResponse(**record)


@router.patch("/{grievance_id}", response_model=AdminGrievanceDetailResponse)
async def update_grievance(
    grievance_id: str,
    payload: AdminGrievanceUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_admin_user),
) -> AdminGrievanceDetailResponse:
    """
    Perform controlled operational update (status transition, priority, or staff assignment).
    Rejects invalid status transitions with HTTP 400.
    Rejects unauthorized access with HTTP 403.
    """
    updates = payload.model_dump(exclude_unset=True)
    try:
        updated = update_admin_grievance(grievance_id, updates, current_user)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance case '{grievance_id}' was not found.",
        )

    logger.info(
        "Grievance %s updated by operator %s: %s",
        grievance_id,
        current_user.get("email"),
        list(updates.keys()),
    )
    return AdminGrievanceDetailResponse(**updated)


@router.post("/{grievance_id}/notes", response_model=AdminGrievanceDetailResponse)
async def add_note_to_grievance(
    grievance_id: str,
    payload: AdminGrievanceNoteRequest,
    current_user: dict[str, Any] = Depends(get_current_admin_user),
) -> AdminGrievanceDetailResponse:
    """
    Append an internal operational verification note to the grievance history.
    Notes remain strictly internal to operations staff and are never exposed publicly.
    """
    try:
        updated = append_grievance_note(grievance_id, payload.note, current_user)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance case '{grievance_id}' was not found.",
        )

    logger.info(
        "Operator %s added note to grievance %s",
        current_user.get("email"),
        grievance_id,
    )
    return AdminGrievanceDetailResponse(**updated)
