"""
Admin Knowledge Document Ingestion & Review Router (Phase 2B.2).

Endpoints:
- POST /api/admin/knowledge/documents: Upload document, validate file, persist to storage, initialize in DRAFT.
- GET  /api/admin/knowledge/documents: List knowledge documents with filters and pagination.
- GET  /api/admin/knowledge/documents/{id}: Retrieve detailed document governance metadata.
- POST /api/admin/knowledge/documents/{id}/review: Transition draft document to UNDER_REVIEW.
- GET  /api/admin/knowledge/documents/{id}/file: Securely retrieve the raw uploaded document.
"""
from __future__ import annotations

import json
import logging
from typing import Optional, List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
    Response,
)

from app.dependencies import get_current_admin_user
from app.schemas.admin_knowledge import (
    AdminKnowledgeDocumentResponse,
    AdminKnowledgeListResponse,
    AdminKnowledgeReviewTransitionRequest,
    AdminKnowledgeStatusResponse,
    AdminKnowledgeVerifyRequest,
    AdminKnowledgePublishRequest,
    AdminKnowledgePublishResponse,
    AdminKnowledgeVersionHistoryResponse,
    AdminKnowledgeReindexRequest,
    AdminKnowledgeReindexResponse,
)
from app.schemas.governance import (
    DocumentType,
    AuthorityLevel,
    Jurisdiction,
    Applicability,
    PrecedenceTier,
)
from database.storage import validate_file_content, read_knowledge_file
from database.repository import (
    create_admin_knowledge_document,
    list_admin_knowledge_documents,
    get_admin_knowledge_document_by_id,
    submit_document_for_review,
    verify_admin_knowledge_document,
    reject_admin_knowledge_document,
    publish_admin_knowledge_document,
    delete_admin_knowledge_document_and_chunks,
    get_admin_knowledge_document_versions,
    reindex_admin_knowledge_document,
    create_audit_log,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/knowledge", tags=["admin-knowledge"])


def _parse_applicability(raw_applicability: Optional[str]) -> List[str]:
    """Parse applicability from form-data (JSON array or comma-separated strings)."""
    if not raw_applicability:
        return ["ALL_COOPERATIVES"]
    clean = raw_applicability.strip()
    if clean.startswith("["):
        try:
            parsed = json.loads(clean)
            if isinstance(parsed, list):
                return [str(item).strip().upper() for item in parsed if str(item).strip()]
        except Exception:
            pass
    parts = [p.strip().upper() for p in clean.split(",") if p.strip()]
    return parts if parts else ["ALL_COOPERATIVES"]


@router.post(
    "/documents",
    response_model=AdminKnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload knowledge document (Created in DRAFT state)",
)
async def upload_knowledge_document(
    file: UploadFile = File(...),
    title: str = Form(..., min_length=3, max_length=300),
    description: Optional[str] = Form(None, max_length=2000),
    document_type: str = Form("GUIDELINE"),
    source_name: Optional[str] = Form(None, max_length=200),
    source_url: Optional[str] = Form(None, max_length=500),
    language: str = Form("en", max_length=10),
    version: Optional[str] = Form(None),
    authority_level: Optional[str] = Form(None),
    jurisdiction: Optional[str] = Form(None),
    applicability: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    effective_date: Optional[str] = Form(None),
    expiry_review_date: Optional[str] = Form(None),
    precedence_tier: int = Form(50),
    current_user: dict = Depends(get_current_admin_user),
) -> AdminKnowledgeDocumentResponse:
    """
    Ingest a new knowledge document.
    Enforces file type inspection, size limits, filename sanitization, and safe storage.
    Initial state is strictly DRAFT with is_current=False.
    Does NOT generate embeddings or insert chunks into citizen RAG index.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    # Read file content
    try:
        content = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read uploaded file content.",
        ) from exc

    # Validate file content & magic bytes
    is_valid, err_msg = validate_file_content(content, file.filename)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg or "File validation failed.",
        )

    # Validate precedence tier
    if precedence_tier < 1 or precedence_tier > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Precedence tier must be an integer between 1 and 100.",
        )

    # Parse applicability list
    app_list = _parse_applicability(applicability)

    # Normalize document type
    norm_doc_type = document_type.strip().upper()
    valid_doc_types = {e.value for e in DocumentType} | {"CIRCULAR", "ORDER", "POLICY", "BYLAWS", "ACT", "RULE", "SCHEME", "GUIDELINE", "MANUAL", "FAQ"}
    if norm_doc_type not in valid_doc_types:
        norm_doc_type = "GUIDELINE"

    # Persist document record and raw file
    operator_id = str(current_user.get("id") or "SYSTEM")
    try:
        doc_record = create_admin_knowledge_document(
            title=title,
            file_bytes=content,
            file_name=file.filename,
            document_type=norm_doc_type,
            description=description,
            source_name=source_name,
            source_url=source_url,
            language=language.strip().lower(),
            version=version,
            authority_level=authority_level.strip().upper() if authority_level else "UNKNOWN",
            jurisdiction=jurisdiction.strip().upper() if jurisdiction else "MAHARASHTRA",
            applicability=app_list,
            year=year,
            effective_date=effective_date,
            expiry_review_date=expiry_review_date,
            precedence_tier=precedence_tier,
            created_by=operator_id,
            content_type=file.content_type,
        )
    except Exception as exc:
        logger.error("Failed to create knowledge document: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist knowledge document: {str(exc)}",
        ) from exc

    logger.info(
        "Operator %s created draft knowledge document id=%s, title='%s'",
        current_user.get("email"),
        doc_record["id"],
        doc_record["title"],
    )

    return AdminKnowledgeDocumentResponse(**doc_record)


@router.get(
    "/documents",
    response_model=AdminKnowledgeListResponse,
    summary="List knowledge documents for Administration",
)
async def list_documents_admin(
    status: Optional[str] = Query(None, description="Filter by status: draft, under_review, published, all"),
    document_type: Optional[str] = Query(None, description="Filter by document taxonomy"),
    language: Optional[str] = Query(None, description="Filter by language code"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    applicability: Optional[str] = Query(None, description="Filter by target society applicability"),
    search: Optional[str] = Query(None, description="Free-text search over title, description, and source"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_admin_user),
) -> AdminKnowledgeListResponse:
    """
    List knowledge documents with comprehensive governance fields, filtering, and pagination.
    Accessible to authenticated ADMIN and STAFF operators.
    """
    result = list_admin_knowledge_documents(
        status=status,
        document_type=document_type,
        language=language,
        jurisdiction=jurisdiction,
        applicability=applicability,
        search=search,
        page=page,
        page_size=page_size,
    )

    items = [AdminKnowledgeDocumentResponse(**item) for item in result["items"]]
    return AdminKnowledgeListResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get(
    "/documents/{id}",
    response_model=AdminKnowledgeDocumentResponse,
    summary="Get single knowledge document details",
)
async def get_document_admin(
    id: str,
    current_user: dict = Depends(get_current_admin_user),
) -> AdminKnowledgeDocumentResponse:
    """
    Retrieve single knowledge document with all governance and file metadata.
    """
    doc = get_admin_knowledge_document_by_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document with id '{id}' was not found.",
        )
    return AdminKnowledgeDocumentResponse(**doc)


@router.post(
    "/documents/{id}/review",
    response_model=AdminKnowledgeStatusResponse,
    summary="Submit DRAFT document for UNDER_REVIEW triage",
)
async def submit_for_review_endpoint(
    id: str,
    body: Optional[AdminKnowledgeReviewTransitionRequest] = None,
    current_user: dict = Depends(get_current_admin_user),
) -> AdminKnowledgeStatusResponse:
    """
    Transition a draft document to UNDER_REVIEW state.
    Only draft documents can be transitioned.
    Publication, approval, and vector indexing are strictly prohibited in this phase.
    """
    notes = body.notes if body else None
    updated_doc, error_msg = submit_document_for_review(
        doc_id=id,
        operator_user=current_user,
        notes=notes,
    )

    if error_msg:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in error_msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=error_msg)

    logger.info(
        "Operator %s transitioned document id=%s to UNDER_REVIEW",
        current_user.get("email"),
        id,
    )

    return AdminKnowledgeStatusResponse(
        status="ok",
        message="Document successfully submitted for administrator review.",
        document=AdminKnowledgeDocumentResponse(**updated_doc),
    )


@router.get(
    "/documents/{id}/file",
    summary="Securely read raw uploaded file",
)
async def get_document_file_endpoint(
    id: str,
    current_user: dict = Depends(get_current_admin_user),
) -> Response:
    """
    Stream or download the original uploaded document for authorized operators.
    """
    doc = get_admin_knowledge_document_by_id(id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    storage_path = doc.get("storage_path")
    if not storage_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File attachment not found for this document.")

    content = read_knowledge_file(storage_path, doc_id=id)
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attached file content could not be located in storage.")

    mime_type = doc.get("mime_type") or "application/octet-stream"
    filename = doc.get("file_name") or f"document_{id}.bin"

    return Response(
        content=content,
        media_type=mime_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.post(
    "/documents/{id}/verify",
    response_model=AdminKnowledgeStatusResponse,
    summary="Explicit ADMIN-only verification of document governance evidence",
)
async def verify_document_endpoint(
    id: str,
    body: Optional[AdminKnowledgeVerifyRequest] = None,
    current_user: dict = Depends(get_current_admin_user),
) -> AdminKnowledgeStatusResponse:
    """
    Explicit ADMIN-only verification of a document in 'under_review' status.
    Validates governance evidence and marks document 'verified'.
    STAFF receives HTTP 403.
    """
    if (current_user.get("role") or "").upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Only administrators have authority to verify knowledge documents.",
        )

    verify_payload = body.model_dump(exclude_unset=True) if body else None
    doc, error_msg, err_code = verify_admin_knowledge_document(
        doc_id=id,
        operator_user=current_user,
        verify_data=verify_payload,
    )

    if error_msg:
        raise HTTPException(status_code=err_code, detail=error_msg)

    logger.info("Administrator %s verified document id=%s", current_user.get("email"), id)
    create_audit_log(
        user=current_user,
        action="DOCUMENT_VERIFIED",
        entity_type="knowledge_document",
        entity_id=id,
        details={
            "title": doc.get("title"),
            "previous_status": "under_review",
            "new_status": "verified",
            "authority_level": doc.get("authority_level"),
            "jurisdiction": doc.get("jurisdiction"),
            "precedence_tier": doc.get("precedence_tier"),
        },
    )
    return AdminKnowledgeStatusResponse(
        status="ok",
        message="Knowledge document successfully verified by administrator.",
        document=AdminKnowledgeDocumentResponse(**doc),
    )


@router.post(
    "/documents/{id}/reject",
    response_model=AdminKnowledgeStatusResponse,
    summary="ADMIN-only rejection of document back to DRAFT",
)
async def reject_document_endpoint(
    id: str,
    body: Optional[AdminKnowledgeReviewTransitionRequest] = None,
    current_user: dict = Depends(get_current_admin_user),
) -> AdminKnowledgeStatusResponse:
    """
    Reject an under-review or verified document back to draft.
    STAFF receives HTTP 403.
    """
    if (current_user.get("role") or "").upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Only administrators have authority to reject knowledge documents.",
        )

    reason = body.notes if body else None
    doc, error_msg, err_code = reject_admin_knowledge_document(
        doc_id=id,
        operator_user=current_user,
        reason=reason,
    )

    if error_msg:
        raise HTTPException(status_code=err_code, detail=error_msg)

    logger.info("Administrator %s rejected document id=%s back to DRAFT", current_user.get("email"), id)
    create_audit_log(
        user=current_user,
        action="DOCUMENT_REJECTED",
        entity_type="knowledge_document",
        entity_id=id,
        details={
            "title": doc.get("title"),
            "previous_status": "under_review",
            "new_status": "draft",
            "reason": reason,
        },
    )
    return AdminKnowledgeStatusResponse(
        status="ok",
        message="Knowledge document returned to draft.",
        document=AdminKnowledgeDocumentResponse(**doc),
    )


@router.post(
    "/documents/{id}/publish",
    response_model=AdminKnowledgePublishResponse,
    summary="Canonical ADMIN-only publication of verified knowledge document",
)
@router.post(
    "/documents/{id}/approve",
    response_model=AdminKnowledgePublishResponse,
    summary="Alias for ADMIN-only publication of verified knowledge document",
)
async def publish_document_endpoint(
    id: str,
    body: Optional[AdminKnowledgePublishRequest] = None,
    current_user: dict = Depends(get_current_admin_user),
) -> AdminKnowledgePublishResponse:
    """
    Staged canonical publication of a VERIFIED knowledge document.
    Extracts text, generates 768-dim embeddings via gemini-embedding-001,
    inserts chunks, and atomically activates the document in live citizen RAG.
    STAFF receives HTTP 403.
    """
    if (current_user.get("role") or "").upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Only administrators have authority to publish knowledge documents.",
        )

    notes = body.notes if body else None
    doc, publish_meta, error_msg, err_code = publish_admin_knowledge_document(
        doc_id=id,
        operator_user=current_user,
        notes=notes,
    )

    if error_msg:
        raise HTTPException(status_code=err_code, detail=error_msg)

    logger.info(
        "Administrator %s successfully published document id=%s with %d chunks",
        current_user.get("email"),
        id,
        publish_meta.get("published_chunks_count", 0),
    )

    create_audit_log(
        user=current_user,
        action="DOCUMENT_PUBLISHED",
        entity_type="knowledge_document",
        entity_id=id,
        details={
            "title": doc.get("title"),
            "version": doc.get("version"),
            "published_chunks_count": publish_meta.get("published_chunks_count", 0),
            "embedding_model": publish_meta.get("embedding_model", "gemini-embedding-001"),
            "vector_dimension": publish_meta.get("vector_dimension", 768),
            "previous_status": "verified",
            "new_status": "published",
        },
    )

    return AdminKnowledgePublishResponse(
        status="ok",
        message="Document published successfully. Chunks and embeddings live in RAG retrieval.",
        published_chunks_count=publish_meta.get("published_chunks_count", 0),
        embedding_model=publish_meta.get("embedding_model", "gemini-embedding-001"),
        vector_dimension=publish_meta.get("vector_dimension", 768),
        document=AdminKnowledgeDocumentResponse(**doc),
    )


@router.delete(
    "/documents/{id}",
    summary="ADMIN-only deletion of document and its chunks for test safety",
)
async def delete_document_endpoint(
    id: str,
    current_user: dict = Depends(get_current_admin_user),
):
    """
    Delete document and associated chunks. ADMIN only.
    """
    if (current_user.get("role") or "").upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Only administrators can delete knowledge documents.",
        )

    delete_admin_knowledge_document_and_chunks(id)
    return {"status": "ok", "message": f"Document {id} and associated chunks deleted successfully."}


@router.get(
    "/documents/{id}/versions",
    response_model=AdminKnowledgeVersionHistoryResponse,
    summary="Get document version lineage and history",
)
async def get_document_versions_endpoint(
    id: str,
    current_user: dict = Depends(get_current_admin_user),
) -> AdminKnowledgeVersionHistoryResponse:
    """
    Retrieve full version history and lineage details for a given document.
    Accessible to authenticated operators (ADMIN and STAFF).
    """
    history, error_msg, err_code = get_admin_knowledge_document_versions(id)
    if error_msg:
        raise HTTPException(status_code=err_code, detail=error_msg)
    return AdminKnowledgeVersionHistoryResponse(**history)


@router.post(
    "/documents/{id}/reindex",
    response_model=AdminKnowledgeReindexResponse,
    summary="Safe ADMIN-only re-indexing of an eligible published and current document",
)
async def reindex_document_endpoint(
    id: str,
    body: Optional[AdminKnowledgeReindexRequest] = None,
    current_user: dict = Depends(get_current_admin_user),
) -> AdminKnowledgeReindexResponse:
    """
    Safely re-index an existing published and current document.
    Enforces that the document is active and published.
    Embeddings are re-generated with gemini-embedding-001 and validated at 768-dim.
    STAFF receives HTTP 403.
    Non-published/non-current documents receive HTTP 400.
    """
    if (current_user.get("role") or "").upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Only administrators have authority to re-index knowledge documents.",
        )

    notes = body.notes if body else None
    result, error_msg, err_code = reindex_admin_knowledge_document(
        doc_id=id,
        operator_user=current_user,
        notes=notes,
    )

    if error_msg:
        raise HTTPException(status_code=err_code, detail=error_msg)

    logger.info(
        "Administrator %s successfully re-indexed document id=%s with %d chunks",
        current_user.get("email"),
        id,
        result.get("chunks_created", 0),
    )

    create_audit_log(
        user=current_user,
        action="DOCUMENT_REINDEXED",
        entity_type="knowledge_document",
        entity_id=id,
        details={
            "version": result.get("version"),
            "chunks_created": result.get("chunks_created", 0),
            "embedding_model": result.get("embedding_model", "gemini-embedding-001"),
            "vector_dimension": result.get("vector_dimension", 768),
            "status": "published",
        },
    )

    return AdminKnowledgeReindexResponse(**result)

