"""
Kiosk Fleet Monitoring & Telemetry Endpoints (Phase 2A.3).

Endpoints:
  POST  /api/kiosks/{id}/heartbeat  → Device M2M telemetry reporting (per-device key)
  GET   /api/admin/kiosks           → Fleet status listing with RBAC & filtering
  GET   /api/admin/kiosks/{id}      → Kiosk telemetry & diagnostic details
  PATCH /api/admin/kiosks/{id}      → Operational status & notes update

SAFETY NOTE:
  Remote reboot, shutdown, or shell execution is strictly NOT implemented.
  This service provides monitoring and telemetry ingestion only.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.dependencies import get_current_admin_user
from app.schemas.admin_kiosk import (
    KioskHeartbeatRequest,
    KioskHeartbeatResponse,
    KioskListResponse,
    KioskResponse,
    KioskUpdateRequest,
)
from database.repository import (
    get_kiosk_by_id,
    list_kiosks,
    process_kiosk_heartbeat,
    update_kiosk_operational,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["kiosks"])


# ── M2M Device Telemetry ───────────────────────────────────────────────────────

@router.post(
    "/api/kiosks/{kiosk_id}/heartbeat",
    response_model=KioskHeartbeatResponse,
    summary="Record kiosk heartbeat telemetry",
)
async def kiosk_heartbeat(
    kiosk_id: str,
    payload: KioskHeartbeatRequest,
    x_kiosk_key: Optional[str] = Header(default=None, alias="X-Kiosk-Key"),
    authorization: Optional[str] = Header(default=None),
) -> KioskHeartbeatResponse:
    """
    M2M Device Heartbeat Endpoint:
    Receives periodic telemetry and diagnostic status from hardware kiosks.
    Authenticated via dedicated per-kiosk key in X-Kiosk-Key or Authorization Bearer.
    """
    # Extract kiosk key
    key = ""
    if x_kiosk_key and x_kiosk_key.strip():
        key = x_kiosk_key.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        key = authorization[7:].strip()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing kiosk authentication key (X-Kiosk-Key or Bearer token required).",
        )

    try:
        res = process_kiosk_heartbeat(kiosk_id, payload.model_dump(), key)
        return KioskHeartbeatResponse(**res)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )


# ── Admin Kiosk Fleet Management ───────────────────────────────────────────────

@router.get(
    "/api/admin/kiosks",
    response_model=KioskListResponse,
    summary="List monitored kiosks with RBAC and filtering",
)
async def get_admin_kiosks(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    district: Optional[str] = Query(default=None, description="Filter by district"),
    state: Optional[str] = Query(default=None, description="Filter by state"),
    pacs: Optional[str] = Query(default=None, description="Filter by PACS society"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (online, offline, maintenance)"),
    search: Optional[str] = Query(default=None, description="Free text search on ID, name, location, PACS"),
    current_user: dict[str, Any] = Depends(get_current_admin_user),
) -> KioskListResponse:
    """
    Fleet monitoring listing:
    - ADMIN: sees all kiosks in the fleet.
    - STAFF: sees only kiosks assigned to their host PACS.
    Calculates deterministic online/offline states based on 15-minute heartbeat threshold.
    """
    try:
        all_items = list_kiosks(
            district=district,
            state=state,
            pacs=pacs,
            status=status_filter,
            search=search,
            user=current_user,
        )
        total = len(all_items)
        start_idx = (page - 1) * page_size
        paged_items = all_items[start_idx : start_idx + page_size]
        return KioskListResponse(
            items=[KioskResponse(**item) for item in paged_items],
            total=total,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )


@router.get(
    "/api/admin/kiosks/{kiosk_id}",
    response_model=KioskResponse,
    summary="Get single kiosk telemetry details",
)
async def get_admin_kiosk_detail(
    kiosk_id: str,
    current_user: dict[str, Any] = Depends(get_current_admin_user),
) -> KioskResponse:
    """
    Retrieve single kiosk diagnostics and hardware telemetry.
    Rejects unauthorized STAFF attempting to access kiosks outside their assigned PACS (403).
    """
    try:
        kiosk = get_kiosk_by_id(kiosk_id, current_user)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    if kiosk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kiosk '{kiosk_id}' not found.",
        )

    return KioskResponse(**kiosk)


@router.patch(
    "/api/admin/kiosks/{kiosk_id}",
    response_model=KioskResponse,
    summary="Update kiosk operational status or operational notes",
)
async def patch_admin_kiosk(
    kiosk_id: str,
    payload: KioskUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_admin_user),
) -> KioskResponse:
    """
    Operational status update:
    Allows operators to mark a device as maintenance or offline, or append field notes.
    Rejects modification of hardware diagnostics, uptime, or identity fields.
    """
    try:
        updated = update_kiosk_operational(
            kiosk_id=kiosk_id,
            status=payload.status,
            notes=payload.notes,
            user=current_user,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kiosk '{kiosk_id}' not found.",
        )

    return KioskResponse(**updated)
