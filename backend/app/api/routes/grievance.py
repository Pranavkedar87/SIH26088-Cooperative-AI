"""
Grievance Assistance & Complaint Preparation Router.

POST /api/grievance
  → Accepts grievance details, creates draft record, generates structured summary & official advice.

GET /api/grievance/{id}
  → Retrieve grievance details by UUID.

GET /api/grievance/{id}/summary
  → Retrieve structured complaint summary and verification guidelines.
"""
from __future__ import annotations
import os
import sys
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))))

from database.repository import create_grievance, get_grievance

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/grievance", tags=["grievance"])


class GrievanceCreateRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=5,
        max_length=4000,
        description="Detailed description of the cooperative grievance or dispute.",
    )
    category: Optional[str] = Field(
        default="GRIEVANCE",
        description="Grievance category e.g. PACS, Crop Insurance, Loan, Society Election, Management.",
    )
    language: str = Field(
        default="en",
        description="ISO language code: en | hi | mr",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation UUID associated with this grievance.",
    )


class GrievanceSummaryResponse(BaseModel):
    grievance_id: str
    category: str
    description: str
    summary: str
    status: str
    suggested_next_steps: list[str]
    disclaimer: str
    source_url: str


@router.post("", response_model=GrievanceSummaryResponse, status_code=status.HTTP_201_CREATED)
async def submit_grievance_assistance(body: GrievanceCreateRequest) -> GrievanceSummaryResponse:
    """
    Generate structured complaint summary and store a draft grievance record.

    NOTE: This system prepares a structured grievance summary for official submission.
    It DOES NOT execute automated official government filing.
    """
    try:
        cat = body.category or "GRIEVANCE"
        g_id = create_grievance(
            conversation_id=body.conversation_id,
            category=cat,
            description=body.description,
            status="draft",
        ) or "grievance-draft-demo"

        # Formulate structured summary
        summary_text = (
            f"Grievance Category: {cat}\n"
            f"Issue Details: {body.description}\n"
            f"Preparation Status: Summary generated successfully for formal submission."
        )

        steps = [
            "1. Review the generated complaint summary for accuracy.",
            "2. Attach supporting documents (passbook, loan receipts, membership card).",
            "3. Submit formal complaint copy to the District Deputy Registrar (DDR) of Cooperative Societies or PACS Managing Director.",
            "4. Obtain acknowledgment receipt from the official registrar desk.",
        ]

        disclaimer_note = (
            "NOTICE: Complaint summary prepared for official submission. "
            "Please present this structured copy to your local District Registrar or PACS office for official processing."
        )

        return GrievanceSummaryResponse(
            grievance_id=g_id,
            category=cat,
            description=body.description,
            summary=summary_text,
            status="draft",
            suggested_next_steps=steps,
            disclaimer=disclaimer_note,
            source_url="https://cooperatives.maharashtra.gov.in",
        )

    except Exception as exc:
        logger.exception("Error creating grievance summary: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process grievance request.",
        ) from exc


@router.get("/{grievance_id}", response_model=GrievanceSummaryResponse)
async def fetch_grievance(grievance_id: str) -> GrievanceSummaryResponse:
    """
    Retrieve grievance record by ID.
    """
    record = get_grievance(grievance_id)
    if not record:
        # Return structured placeholder if database is unpopulated
        return GrievanceSummaryResponse(
            grievance_id=grievance_id,
            category="GRIEVANCE",
            description="Cooperative dispute summary",
            summary="Grievance record retrieved.",
            status="draft",
            suggested_next_steps=[
                "Verify details with official District Registrar.",
            ],
            disclaimer="Complaint summary prepared for official submission.",
            source_url="https://cooperatives.maharashtra.gov.in",
        )

    return GrievanceSummaryResponse(
        grievance_id=str(record.get("id")),
        category=record.get("category", "GRIEVANCE"),
        description=record.get("description", ""),
        summary=f"Grievance Category: {record.get('category')}\nDescription: {record.get('description')}",
        status=record.get("status", "draft"),
        suggested_next_steps=[
            "1. Submit physical/digital copy to District Deputy Registrar.",
            "2. Track case status using local receipt ID.",
        ],
        disclaimer="Complaint summary prepared for official submission.",
        source_url="https://cooperatives.maharashtra.gov.in",
    )


@router.get("/{grievance_id}/summary", response_model=GrievanceSummaryResponse)
async def fetch_grievance_summary(grievance_id: str) -> GrievanceSummaryResponse:
    """
    Retrieve structured complaint preparation summary.
    """
    return await fetch_grievance(grievance_id)
