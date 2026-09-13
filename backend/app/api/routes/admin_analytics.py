"""
Admin Analytics & Operational Insights Router (Phase 2C.1).

Endpoints:
- GET /api/admin/analytics/overview: Comprehensive database-backed metrics for queries, languages, intents, kiosks, grievances, and knowledge.
- GET /api/admin/analytics/knowledge-gaps: Systematically derived knowledge gaps and AI escalations.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import require_admin_role
from app.schemas.admin_analytics import (
    AdminAnalyticsOverviewResponse,
    AdminKnowledgeGapsResponse,
)
from database.repository import (
    get_admin_analytics_overview,
    get_admin_knowledge_gaps,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/analytics", tags=["admin-analytics"])


@router.get("/overview", response_model=AdminAnalyticsOverviewResponse)
async def get_analytics_overview(
    period: str = Query(
        default="30d",
        pattern="^(24h|7d|30d)$",
        description="Reporting period window: 24h, 7d, or 30d",
    ),
    current_user: dict[str, Any] = Depends(require_admin_role(["ADMIN"])),
) -> AdminAnalyticsOverviewResponse:
    """
    Retrieve real database-backed operational metrics (ADMIN only):
    - User query volume, timeline points, and period filters (24h, 7d, 30d)
    - Multilingual adoption distribution from user messages
    - Intent domain classification distribution from assistant responses
    - Grievance resolution status breakdown
    - Knowledge document governance state metrics
    - Kiosk hardware fleet telemetry status
    - Explicit non-collected channel telemetry notice
    """
    try:
        data = get_admin_analytics_overview(period=period, user=current_user)
        return AdminAnalyticsOverviewResponse(**data)
    except Exception as exc:
        logger.error("Failed to generate admin analytics overview: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics overview: {str(exc)}",
        )


@router.get("/knowledge-gaps", response_model=AdminKnowledgeGapsResponse)
async def get_knowledge_gaps(
    current_user: dict[str, Any] = Depends(require_admin_role(["ADMIN"])),
) -> AdminKnowledgeGapsResponse:
    """
    Retrieve real database-derived knowledge gaps and AI escalations (ADMIN only):
    - Uncovered citizen query intents without official published documentation
    - Recurring grievance complaint categories
    """
    try:
        data = get_admin_knowledge_gaps(user=current_user)
        return AdminKnowledgeGapsResponse(**data)
    except Exception as exc:
        logger.error("Failed to generate admin knowledge gaps: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate knowledge gaps: {str(exc)}",
        )
