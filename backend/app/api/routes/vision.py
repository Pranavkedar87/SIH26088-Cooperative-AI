"""
Hardware & Web Vision / Camera Endpoint Contract.

POST /api/vision/query

FUTURE CAMERA ARCHITECTURE:
  - ESP32-CAM or Web Camera captures document / application photo.
  - Image is sent to FastAPI /api/vision/query.
  - OCR extracts text, then delegates query to `services.query_service.process_user_query`.
"""
from __future__ import annotations
import logging
import os
import sys
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.schemas.query import QueryResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))))

from services.query_service import process_user_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vision", tags=["vision"])


class VisionQueryRequest(BaseModel):
    extracted_text: str = Field(
        ...,
        description="Text extracted via OCR from document photo or camera capture.",
    )
    language: str = Field(
        default="en",
        description="ISO language code: en | hi | mr",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session UUID.",
    )
    device_id: Optional[str] = Field(
        default=None,
        description="Camera / ESP32-CAM device identifier.",
    )


@router.post("/query", response_model=QueryResponse)
async def vision_query(body: VisionQueryRequest) -> QueryResponse:
    """
    Camera / OCR Vision Query Endpoint.

    Delegates OCR text analysis through the central `process_user_query` AI/RAG pipeline.
    """
    try:
        logger.info("Vision Query received | device_id=%s | lang=%s", body.device_id, body.language)
        return await process_user_query(
            message=body.extracted_text,
            language=body.language,
            session_id=body.session_id,
        )
    except Exception as exc:
        logger.exception("Error in /api/vision/query: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing vision request.",
        ) from exc
