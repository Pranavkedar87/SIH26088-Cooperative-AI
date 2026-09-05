"""
Knowledge Discovery & Document List Endpoints.

GET /api/knowledge/documents
  → List all official knowledge documents stored in the database.

GET /api/knowledge/search
  → Vector search knowledge chunks with similarity score.
"""
from __future__ import annotations
import os
import sys
import logging
from typing import Optional

from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))))

from database.repository import get_knowledge_documents
from rag.retriever import retrieve_relevant_knowledge, RetrievedChunk

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class DocumentItem(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    document_type: Optional[str] = None
    language: Optional[str] = None


class RetrievedChunkItem(BaseModel):
    content: str
    document_id: str
    title: str
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    document_type: Optional[str] = None
    language: Optional[str] = None
    similarity: float


class KnowledgeSearchResult(BaseModel):
    query: str
    language: str
    chunks: list[RetrievedChunkItem]
    count: int


@router.get("/documents", response_model=list[DocumentItem])
async def list_documents() -> list[DocumentItem]:
    """
    List all official cooperative documents registered in the knowledge base.
    """
    try:
        db_docs = get_knowledge_documents()
        if db_docs:
            return [
                DocumentItem(
                    id=str(d.get("id", "")),
                    title=d.get("title", "Official Source"),
                    description=d.get("description"),
                    source_name=d.get("source_name"),
                    source_url=d.get("source_url"),
                    document_type=d.get("document_type"),
                    language=d.get("language"),
                )
                for d in db_docs
            ]

        # Fallback list from knowledge base files metadata
        kb_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "knowledge_base"))
        docs = []
        if os.path.exists(kb_dir):
            import json
            for root, _, files in os.walk(kb_dir):
                for file_name in files:
                    if file_name.endswith(".json"):
                        file_path = os.path.join(root, file_name)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                docs.append(
                                    DocumentItem(
                                        title=data.get("title", file_name),
                                        description=data.get("description", "Cooperative guidance document"),
                                        source_name=data.get("source_name", "Government Authority"),
                                        source_url=data.get("source_url"),
                                        document_type=data.get("document_type", "guidelines"),
                                        language=data.get("language", "en"),
                                    )
                                )
                        except Exception:
                            continue
        return docs

    except Exception as exc:
        logger.error("Error in GET /api/knowledge/documents: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to list knowledge documents.",
        ) from exc


@router.get("/search", response_model=KnowledgeSearchResult)
async def search_knowledge(
    q: str = Query(..., min_length=2, description="Search query string"),
    language: str = Query("en", description="Language code: en | hi | mr"),
    intent: Optional[str] = Query(None, description="Optional intent filter"),
    top_k: int = Query(4, ge=1, le=10, description="Max result count"),
) -> KnowledgeSearchResult:
    """
    Search official knowledge base using vector similarity search.
    """
    try:
        chunks = retrieve_relevant_knowledge(
            query=q,
            language=language,
            intent=intent,
            top_k=top_k,
            match_threshold=0.40,
        )
        chunk_items = [
            RetrievedChunkItem(
                content=c.get("content", ""),
                document_id=str(c.get("document_id", "")),
                title=c.get("title", "Official Document"),
                source_name=c.get("source_name"),
                source_url=c.get("source_url"),
                document_type=c.get("document_type"),
                language=c.get("language"),
                similarity=float(c.get("similarity", 0.0)),
            )
            for c in chunks
        ]
        return KnowledgeSearchResult(
            query=q,
            language=language,
            chunks=chunk_items,
            count=len(chunk_items),
        )
    except Exception as exc:
        logger.error("Error in GET /api/knowledge/search: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to perform knowledge search.",
        ) from exc
