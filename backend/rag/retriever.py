"""
Knowledge retriever module.

Performs vector similarity search against Supabase pgvector knowledge_chunks.
Includes graceful Python cosine-similarity fallback if RPC function is missing.
"""
from __future__ import annotations

import math
import logging
from typing import Optional
try:
    from typing_extensions import TypedDict
except ImportError:
    from typing import TypedDict  # type: ignore[assignment]

from database.supabase import get_supabase_client
from rag.embeddings import GeminiEmbeddingProvider

logger = logging.getLogger(__name__)


class RetrievedChunk(TypedDict):
    content: str
    document_id: str
    title: str
    source_name: Optional[str]
    source_url: Optional[str]
    document_type: Optional[str]
    language: Optional[str]
    similarity: float


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


INTENT_ALLOWED_DOC_TYPES: dict[str, set[str]] = {
    "PMFBY": {"scheme_guide", "guide", "pmfby_guide"},
    "AGRICULTURAL_SUPPORT": {"scheme_guide", "guide", "pacs_guide"},
    "COOPERATIVE_LAW": {"legal_act", "act", "guide"},
    "COOPERATIVE_BYLAW": {"legal_act", "bylaw", "guide"},
    "PACS_SERVICE": {"pacs_guide", "service_guide", "guide"},
    "FINANCIAL_LITERACY": {"financial_guide", "guide"},
    "GRIEVANCE": {"legal_act", "guide", "pacs_guide", "scheme_guide"},
}


def _is_doc_type_allowed(doc_type: Optional[str], intent: Optional[str]) -> bool:
    """Return True if doc_type matches the target intent domain."""
    if not intent or intent not in INTENT_ALLOWED_DOC_TYPES:
        return True
    if not doc_type:
        return True
    allowed = INTENT_ALLOWED_DOC_TYPES[intent]
    return doc_type in allowed


def retrieve_relevant_knowledge(
    query: str,
    language: str = "en",
    intent: Optional[str] = None,
    top_k: int = 4,
    match_threshold: float = 0.45,
) -> list[RetrievedChunk]:
    """
    Retrieve top_k knowledge chunks matching the query.

    Steps:
      1. Embed query text using GeminiEmbeddingProvider.
      2. Call Supabase RPC `match_knowledge_chunks`.
      3. Fallback to client-side similarity if RPC fails.
      4. Filter by match_threshold and document domain allowed types.
    """
    if not query or not query.strip():
        return []

    client = get_supabase_client()
    if client is None:
        logger.warning("Supabase client unavailable. Skipping knowledge retrieval.")
        return []

    # 1. Generate query embedding
    embedding_provider = GeminiEmbeddingProvider()
    try:
        query_vec = embedding_provider.embed_text(query)
    except Exception as exc:
        logger.error("Failed to generate query embedding: %s", exc)
        return []

    if not query_vec or all(v == 0.0 for v in query_vec):
        logger.warning("Query vector is empty or zero.")
        return []

    results: list[RetrievedChunk] = []

    # 2. Try Supabase RPC match_knowledge_chunks
    try:
        rpc_response = client.rpc(
            "match_knowledge_chunks",
            {
                "query_embedding": query_vec,
                "match_threshold": match_threshold,
                "match_count": top_k * 2,  # fetch candidate pool
                "filter_language": language,
                "filter_intent": intent,
            },
        ).execute()

        if rpc_response and rpc_response.data:
            for item in rpc_response.data:
                doc_type = item.get("document_type")
                if not _is_doc_type_allowed(doc_type, intent):
                    continue
                results.append({
                    "content": item.get("content", ""),
                    "document_id": str(item.get("document_id", "")),
                    "title": item.get("title", "Official Source"),
                    "source_name": item.get("source_name"),
                    "source_url": item.get("source_url"),
                    "document_type": doc_type,
                    "language": item.get("language"),
                    "similarity": float(item.get("similarity", 0.0)),
                })
                if len(results) >= top_k:
                    break
            if results:
                logger.info("Retrieved %d domain-filtered chunks via RPC match_knowledge_chunks", len(results))
                return results

    except Exception as rpc_exc:
        logger.debug("RPC match_knowledge_chunks failed, falling back to query: %s", rpc_exc)

    # 3. Fallback: Query knowledge_chunks + knowledge_documents directly
    try:
        data = client.table("knowledge_chunks").select(
            "id, document_id, content, language, metadata, "
            "knowledge_documents(title, source_name, source_url, document_type)"
        ).execute()

        if not data or not data.data:
            return []

        scored_chunks: list[tuple[float, dict]] = []
        for row in data.data:
            meta = row.get("metadata") or {}
            chunk_vec = meta.get("embedding") if isinstance(meta, dict) else None

            if not chunk_vec:
                continue

            # Ensure embedding is a list of floats
            if isinstance(chunk_vec, str):
                import json
                try:
                    chunk_vec = json.loads(chunk_vec)
                except Exception:
                    continue

            doc = row.get("knowledge_documents") or {}
            doc_type = doc.get("document_type") or meta.get("document_type")

            if not _is_doc_type_allowed(doc_type, intent):
                continue

            sim = _cosine_similarity(query_vec, chunk_vec)
            if sim >= match_threshold:
                # Boost language match slightly
                if row.get("language") == language:
                    sim += 0.05
                scored_chunks.append((sim, {
                    "content": row.get("content", ""),
                    "document_id": str(row.get("document_id", "")),
                    "title": doc.get("title", "Official Source"),
                    "source_name": doc.get("source_name"),
                    "source_url": doc.get("source_url"),
                    "document_type": doc_type,
                    "language": row.get("language"),
                    "similarity": round(sim, 4),
                }))

        # Sort by similarity desc
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        for sim, chunk in scored_chunks[:top_k]:
            results.append(chunk)

        logger.info("Retrieved %d chunks via Python similarity fallback", len(results))
        return results

    except Exception as exc:
        logger.error("Failed to retrieve knowledge chunks via fallback: %s", exc)
        return []

