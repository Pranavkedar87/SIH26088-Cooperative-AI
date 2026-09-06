"""
Knowledge retriever module for SahkaarSetu (SIH26088).

Performs vector similarity search against Supabase pgvector knowledge_chunks,
with instant domain-grounded local knowledge fallback.
"""
from __future__ import annotations

import math
import logging
import time
from typing import Optional
try:
    from typing_extensions import TypedDict
except ImportError:
    from typing import TypedDict  # type: ignore[assignment]

from database.supabase import get_supabase_client
from rag.embeddings import GeminiEmbeddingProvider

logger = logging.getLogger(__name__)

_CHUNKS_CACHE: list[dict] = []
_CACHE_TIMESTAMP: float = 0.0
_CACHE_TTL_SECONDS: float = 300.0  # 5 minutes cache


class RetrievedChunk(TypedDict):
    content: str
    document_id: str
    title: str
    source_name: Optional[str]
    source_url: Optional[str]
    document_type: Optional[str]
    language: Optional[str]
    similarity: float


# Grounded domain knowledge documents repository for local retrieval
LOCAL_KNOWLEDGE_DOCUMENTS: list[dict[str, Any]] = [
    {
        "title": "PACS Short-Term Crop Loan & Scale of Finance Manual",
        "source_name": "Ministry of Cooperation / NABARD",
        "source_url": "https://cooperation.gov.in/pacs-credit-guidelines",
        "document_id": "doc-pacs-credit-001",
        "document_type": "pacs_guide",
        "keywords": ["loan", "acres", "acre", "land", "pacs", "kcc", "crop loan", "कर्ज", "जमीन", "एकर", "पिक कर्ज"],
        "content": "Primary Agricultural Credit Societies (PACS) provide short-term crop loans to farmer members based on local District Scale of Finance and land holdings (7/12 & 8A extracts). Applicable 3% Interest Subvention Scheme provides subsidy for prompt repayment.",
    },
    {
        "title": "Ministry of Cooperation Policy Framework & Governance Guide",
        "source_name": "Ministry of Cooperation (Govt of India)",
        "source_url": "https://cooperation.gov.in",
        "document_id": "doc-moc-001",
        "document_type": "policy_guide",
        "keywords": ["ministry of cooperation", "ministry", "cooperation", "सहकार मंत्रालय", "सहकारिता मंत्रालय"],
        "content": "The Ministry of Cooperation was formed in July 2021 by the Government of India to provide a dedicated administrative, legal, and policy framework for strengthening cooperative movement in India.",
    },
    {
        "title": "PMFBY Operational Guidelines & Crop Damage Claim Manual",
        "source_name": "Ministry of Agriculture & Farmers Welfare",
        "source_url": "https://pmfby.gov.in",
        "document_id": "doc-pmfby-001",
        "document_type": "pmfby_guide",
        "keywords": ["pmfby", "fasal bima", "crop insurance", "deadline", "फसल बीमा", "पीक विमा", "पिक विमा"],
        "content": "Pradhan Mantri Fasal Bima Yojana (PMFBY) covers crop damage due to non-preventable natural risks. Enrollment and claim deadlines are published season-wise.",
    },
    {
        "title": "Maharashtra Cooperative Societies Act 1960 & Society By-Laws",
        "source_name": "Maharashtra State Cooperative Department",
        "source_url": "https://maharashtra.gov.in",
        "document_id": "doc-mcs-1960",
        "document_type": "legal_act",
        "keywords": ["by-law", "bylaw", "cooperative law", "act", "section", "कायदा", "उपनियम"],
        "content": "Governance of primary cooperative societies, PACS member rights, share capital allocation, dispute resolution, and audit procedures under the MCS Act 1960.",
    },
]


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
    "PMFBY": {"scheme_guide", "guide", "pmfby_guide", "policy_guide"},
    "AGRICULTURAL_SUPPORT": {"scheme_guide", "policy_guide", "educational_guide", "guide", "pacs_guide"},
    "COOPERATIVE_LAW": {"legal_act", "act", "guide", "policy_guide"},
    "COOPERATIVE_BYLAW": {"legal_act", "bylaw", "guide", "policy_guide"},
    "PACS_SERVICE": {"policy_guide", "pacs_guide", "service_guide", "educational_guide", "guide"},
    "FINANCIAL_LITERACY": {"educational_guide", "financial_guide", "policy_guide", "guide"},
    "GRIEVANCE": {"legal_act", "guide", "pacs_guide", "scheme_guide", "policy_guide", "educational_guide"},
}


def _is_doc_type_allowed(doc_type: Optional[str], intent: Optional[str]) -> bool:
    """Return True if doc_type matches the target intent domain."""
    if not intent or intent not in INTENT_ALLOWED_DOC_TYPES:
        return True
    if not doc_type:
        return True
    allowed = INTENT_ALLOWED_DOC_TYPES[intent]
    return doc_type in allowed


def _get_cached_chunks(client) -> list[dict]:
    """Retrieve and cache knowledge chunks in memory to avoid repetitive heavy DB table scans."""
    global _CHUNKS_CACHE, _CACHE_TIMESTAMP
    now = time.time()
    if _CHUNKS_CACHE and (now - _CACHE_TIMESTAMP) < _CACHE_TTL_SECONDS:
        return _CHUNKS_CACHE

    try:
        data = client.table("knowledge_chunks").select(
            "id, document_id, content, language, metadata, "
            "knowledge_documents(title, source_name, source_url, document_type)"
        ).execute()

        if not data or not data.data:
            return _CHUNKS_CACHE

        new_cache = []
        for row in data.data:
            meta = row.get("metadata") or {}
            chunk_vec = meta.get("embedding") if isinstance(meta, dict) else None

            if not chunk_vec:
                continue

            if isinstance(chunk_vec, str):
                import json
                try:
                    chunk_vec = json.loads(chunk_vec)
                except Exception:
                    continue

            doc = row.get("knowledge_documents") or {}
            doc_type = doc.get("document_type") or meta.get("document_type")

            new_cache.append({
                "id": row.get("id"),
                "content": row.get("content", ""),
                "document_id": str(row.get("document_id", "")),
                "title": doc.get("title", "Official Source"),
                "source_name": doc.get("source_name"),
                "source_url": doc.get("source_url"),
                "document_type": doc_type,
                "language": row.get("language"),
                "embedding": chunk_vec,
            })

        _CHUNKS_CACHE = new_cache
        _CACHE_TIMESTAMP = now
        logger.info("Loaded %d knowledge chunks into memory cache", len(_CHUNKS_CACHE))
    except Exception as exc:
        logger.error("Error refreshing knowledge chunks cache: %s", exc)

    return _CHUNKS_CACHE


def retrieve_relevant_knowledge(
    query: str,
    language: str = "en",
    intent: Optional[str] = None,
    top_k: int = 4,
    match_threshold: float = 0.45,
) -> list[RetrievedChunk]:
    """
    Retrieve top_k knowledge chunks matching the query.
    Performs vector similarity search against Supabase, falling back to grounded domain documents repository.
    """
    if not query or not query.strip():
        return []

    results: list[RetrievedChunk] = []

    # 1. Try Supabase pgvector search
    client = get_supabase_client()
    if client is not None:
        embedding_provider = GeminiEmbeddingProvider()
        try:
            query_vec = embedding_provider.embed_text(query)
            if query_vec and any(v != 0.0 for v in query_vec):
                # Try RPC match_knowledge_chunks
                rpc_response = client.rpc(
                    "match_knowledge_chunks",
                    {
                        "query_embedding": query_vec,
                        "match_threshold": match_threshold,
                        "match_count": top_k * 2,
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
        except Exception as exc:
            logger.debug("Supabase RPC vector search unavailable: %s", exc)

    # 2. Match local domain knowledge documents repository if Supabase vector DB yields 0 chunks
    q_lower = query.lower().strip()
    for doc in LOCAL_KNOWLEDGE_DOCUMENTS:
        if any(kw in q_lower for kw in doc["keywords"]):
            results.append({
                "content": doc["content"],
                "document_id": doc["document_id"],
                "title": doc["title"],
                "source_name": doc["source_name"],
                "source_url": doc["source_url"],
                "document_type": doc["document_type"],
                "language": language,
                "similarity": 0.95,
            })
            if len(results) >= top_k:
                break

    if results:
        logger.info("Retrieved %d grounded domain knowledge chunks from local repository", len(results))

    return results
