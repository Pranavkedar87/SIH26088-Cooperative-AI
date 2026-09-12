"""
Knowledge retriever module for SahkaarSetu (SIH26088).

Performs vector similarity search against Supabase pgvector knowledge_chunks,
with instant domain-grounded local knowledge fallback.
"""
from __future__ import annotations

import math
import logging
import re
import time
import os
import json
import glob
from typing import Any, Optional
try:
    from typing_extensions import TypedDict
except ImportError:
    from typing import TypedDict  # type: ignore[assignment]

from database.supabase import get_supabase_client
from rag.embeddings import GeminiEmbeddingProvider, EMBEDDING_DIMENSION

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
    authority_level: Optional[str]
    jurisdiction: Optional[str]
    applicability: Optional[list[str]]
    currentness_status: Optional[str]
    verification_status: Optional[str]
    precedence_tier: Optional[int]
    year: Optional[int]
    page_number: Optional[str]
    section_number: Optional[str]


# Grounded domain knowledge documents repository for local retrieval
LOCAL_KNOWLEDGE_DOCUMENTS: list[dict[str, Any]] = [
    {
        "title": "Model By-Laws of Cooperative Housing Societies (Maharashtra)",
        "source_name": "Department of Co-operation, Govt of Maharashtra",
        "source_url": "https://cooperatives.maharashtra.gov.in",
        "document_id": "doc-housing-bylaw-001",
        "document_type": "bylaw",
        "authority_level": "STATE_GOVERNMENT",
        "jurisdiction": "MAHARASHTRA",
        "applicability": ["HOUSING"],
        "year": 2014,
        "verification_status": "OFFICIAL_NEEDS_VERIFICATION",
        "currentness_status": "NEEDS_VERIFICATION",
        "precedence_tier": 60,
        "section_number": "By-law 65, 79, 91",
        "keywords": ["housing", "housing society", "flat", "maintenance", "cooperative housing", "गृहनिर्माण", "सोसायटी", "management rules"],
        "content": "Model By-Laws of Cooperative Housing Societies in Maharashtra govern member rights, maintenance charge apportionment, managing committee election guidelines, and transfer premium caps (maximum Rs 25,000 as per state statutory circular). Disputes relating to society management must be referred to the Cooperative Court or Deputy Registrar under Section 91 of the MCS Act. Cooperative Housing Society rules operate separately from agricultural credit societies.",
    },
    {
        "title": "Model By-Laws for Primary Agricultural Credit Societies (PACS)",
        "source_name": "Ministry of Cooperation, Govt of India",
        "source_url": "https://cooperation.gov.in",
        "document_id": "doc-pacs-model-bylaws-001",
        "document_type": "bylaw",
        "authority_level": "CENTRAL_GOVERNMENT",
        "jurisdiction": "INDIA",
        "applicability": ["PACS"],
        "year": 2022,
        "verification_status": "OFFICIAL_NEEDS_VERIFICATION",
        "currentness_status": "NEEDS_VERIFICATION",
        "precedence_tier": 60,
        "section_number": "Chapter IV: Board Powers & Duties",
        "keywords": ["pacs by-law", "pacs board", "responsibilities of a pacs board", "board of directors", "pacs committee", "पैक्स उपनियम", "पॅक्स संचालक"],
        "content": "Model By-Laws for Primary Agricultural Credit Societies (PACS) issued by the Ministry of Cooperation provide guidelines on the governance and responsibilities of the PACS Board of Directors: approving member loan applications, managing loan recovery, supervising staff, diversifying into multi-purpose activities (fertilizer, seeds, custom hiring centers), maintaining accounting books, convening annual general meetings (AGM), and ensuring statutory audit compliance. Note: Model By-laws serve as an advisory template until formally adopted by each state or individual society general body.",
    },
    {
        "title": "Maharashtra Cooperative Societies Act 1960 — Member Rights & Governance",
        "source_name": "Department of Co-operation, Marketing & Textiles, Govt of Maharashtra",
        "source_url": "https://cooperatives.maharashtra.gov.in",
        "document_id": "doc-mcs-1960",
        "document_type": "ACT",
        "authority_level": "STATE_GOVERNMENT",
        "jurisdiction": "MAHARASHTRA",
        "applicability": ["ALL_COOPERATIVES"],
        "year": 1960,
        "verification_status": "OFFICIAL_NEEDS_VERIFICATION",
        "currentness_status": "NEEDS_VERIFICATION",
        "precedence_tier": 100,
        "section_number": "Section 81, Section 91",
        "keywords": ["by-law", "bylaw", "cooperative law", "act", "section", "audit", "कायदा", "उपनियम"],
        "content": "The Maharashtra Cooperative Societies Act, 1960 governs the registration, regulation, management, and audit of all cooperative societies in the state of Maharashtra. Section 81 mandates that every society must have its accounts audited at least once every financial year by an auditor approved by the Registrar. Section 91 governs dispute resolution before Cooperative Courts.",
    },
    {
        "title": "PACS Short-Term Crop Loan & Scale of Finance Manual",
        "source_name": "Ministry of Cooperation / NABARD",
        "source_url": "https://cooperation.gov.in/pacs-credit-guidelines",
        "document_id": "doc-pacs-credit-001",
        "document_type": "pacs_guide",
        "authority_level": "CENTRAL_GOVERNMENT",
        "jurisdiction": "INDIA",
        "applicability": ["PACS"],
        "year": None,
        "verification_status": "OFFICIAL_NEEDS_VERIFICATION",
        "currentness_status": "NEEDS_VERIFICATION",
        "precedence_tier": 60,
        "section_number": None,
        "keywords": ["loan", "acres", "acre", "land", "pacs", "kcc", "crop loan", "कर्ज", "जमीन", "एकर", "पिक कर्ज"],
        "content": "Primary Agricultural Credit Societies (PACS) provide short-term crop loans to farmer members based on local District Scale of Finance and land holdings (7/12 & 8A extracts). Applicable 3% Interest Subvention Scheme provides subsidy for prompt repayment.",
    },
    {
        "title": "PMFBY Operational Guidelines & Crop Damage Claim Manual",
        "source_name": "Ministry of Agriculture & Farmers Welfare",
        "source_url": "https://pmfby.gov.in",
        "document_id": "doc-pmfby-001",
        "document_type": "pmfby_guide",
        "authority_level": "CENTRAL_GOVERNMENT",
        "jurisdiction": "INDIA",
        "applicability": ["ALL_COOPERATIVES"],
        "year": None,
        "verification_status": "OFFICIAL_NEEDS_VERIFICATION",
        "currentness_status": "NEEDS_VERIFICATION",
        "precedence_tier": 70,
        "section_number": "Clause 15: Claim Intimation",
        "keywords": ["pmfby", "fasal bima", "crop insurance", "deadline", "72 hours", "फसल बीमा", "पीक विमा", "पिक विमा"],
        "content": "Pradhan Mantri Fasal Bima Yojana (PMFBY) covers crop damage due to non-preventable natural risks. Farmers must intimate localized crop loss within 72 hours of occurrence through the PMFBY Crop Insurance App, nearest bank branch, PACS, or official portal.",
    },
    {
        "title": "Sub-Mission on Agricultural Mechanization (SMAM) & Tractor Subsidy Guidelines",
        "source_name": "Ministry of Agriculture & Farmers Welfare / MahaDBT",
        "source_url": "https://mahadbt.maharashtra.gov.in",
        "document_id": "doc-smam-tractor-001",
        "document_type": "mechanization_guide",
        "authority_level": "CENTRAL_GOVERNMENT",
        "jurisdiction": "INDIA",
        "applicability": ["ALL_COOPERATIVES"],
        "year": None,
        "verification_status": "OFFICIAL_NEEDS_VERIFICATION",
        "currentness_status": "NEEDS_VERIFICATION",
        "precedence_tier": 70,
        "section_number": None,
        "keywords": ["tractor", "mechanization", "farm machinery", "machinery", "sub-mission", "smam", "ट्रॅक्टर", "अनुदान", "यांत्रिकीकरण", "ट्रैक्टर", "सब्सिडी"],
        "content": "Sub-Mission on Agricultural Mechanization (SMAM) and MahaDBT portal provide 40% to 50% subsidy for purchasing tractors, agricultural machinery, and establishing custom hiring centers for small, marginal, SC/ST, and women farmers. Required documents include 7/12 extract, 8A record, Aadhaar card, bank passbook, and dealer quotation. Note: Subsidy percentages and allocation caps are subject to state department annual circulars.",
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
    "PMFBY": {"scheme_guide", "guide", "pmfby_guide", "policy_guide", "SCHEME"},
    "AGRICULTURAL_SUPPORT": {"scheme_guide", "policy_guide", "mechanization_guide", "educational_guide", "guide", "pacs_guide", "SCHEME"},
    "MINISTRY_SCHEME": {"scheme_guide", "policy_guide", "mechanization_guide", "educational_guide", "guide", "pacs_guide", "SCHEME"},
    "COOPERATIVE_LAW": {"legal_act", "act", "guide", "policy_guide", "ACT"},
    "COOPERATIVE_BYLAW": {"legal_act", "bylaw", "guide", "policy_guide", "BYLAW", "ACT"},
    "PACS_SERVICE": {"policy_guide", "pacs_guide", "service_guide", "educational_guide", "guide", "FAQ", "BYLAW"},
    "FINANCIAL_LITERACY": {"educational_guide", "financial_guide", "policy_guide", "guide", "GUIDELINE", "FAQ"},
    "GRIEVANCE": {"legal_act", "guide", "pacs_guide", "scheme_guide", "policy_guide", "educational_guide", "ACT", "BYLAW"},
}


def _is_doc_type_allowed(doc_type: Optional[str], intent: Optional[str]) -> bool:
    """Return True if doc_type matches the target intent domain."""
    if not doc_type:
        return True
    if intent and intent in INTENT_ALLOWED_DOC_TYPES:
        allowed = INTENT_ALLOWED_DOC_TYPES[intent]
        return doc_type in allowed
    # For unspecified or general intents, legal_act is strictly restricted to legal/bylaw/grievance intents
    if doc_type in {"legal_act", "act", "bylaw", "ACT", "BYLAW"} and intent not in {"COOPERATIVE_LAW", "COOPERATIVE_BYLAW", "GRIEVANCE", "GENERAL_COOPERATIVE"}:
        return False
    return True


def _is_applicability_allowed(chunk: dict, query: str) -> bool:
    """
    Strict applicability and domain separation filter:
    - Housing questions MUST NEVER be answered with PACS documents.
    - PACS questions MUST NEVER be answered with Housing documents.
    - PMFBY questions MUST NEVER be answered with Housing documents.
    """
    q_lower = query.lower()
    app_list = chunk.get("applicability") or ["UNKNOWN"]

    is_housing_query = any(w in q_lower for w in ["housing", "गृहनिर्माण", "flat", "flats", "society maintenance", "transfer fee"])
    is_pacs_query = any(w in q_lower for w in ["pacs", "पैक्स", "पॅक्स", "primary agricultural credit"])
    is_crop_insurance_query = any(w in q_lower for w in ["pmfby", "crop insurance", "fasal bima", "पीक विमा", "पिक विमा", "crop damage", "crop loss"])

    # 1. Housing query: Reject PACS-only documents
    if is_housing_query:
        if "PACS" in app_list and "HOUSING" not in app_list and "ALL_COOPERATIVES" not in app_list:
            return False
        # Do not return crop insurance scheme for housing rules
        if chunk.get("document_type") in {"pmfby_guide", "scheme_guide", "SCHEME"}:
            return False

    # 2. PACS query: Reject Housing-only documents
    if is_pacs_query:
        if "HOUSING" in app_list and "PACS" not in app_list and "ALL_COOPERATIVES" not in app_list:
            return False

    # 3. Crop insurance query: Reject Housing documents
    if is_crop_insurance_query:
        if "HOUSING" in app_list:
            return False

    return True


def _load_governance_metadata() -> dict:
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "knowledge_base")
    meta_map = {}
    for filepath in glob.glob(os.path.join(base_dir, "**/*.json"), recursive=True):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                title = data.get("title")
                if title:
                    meta_map[title] = {
                        "document_type": data.get("document_type", "UNKNOWN"),
                        "authority_level": data.get("authority_level", "UNKNOWN"),
                        "jurisdiction": data.get("jurisdiction", "UNKNOWN"),
                        "applicability": data.get("applicability", ["UNKNOWN"]),
                        "currentness_status": data.get("currentness_status", "NEEDS_VERIFICATION"),
                        "verification_status": data.get("verification_status", "NEEDS_VERIFICATION"),
                        "precedence_tier": data.get("precedence_tier", 10),
                        "year": data.get("year", None),
                        "page_number": data.get("page_number"),
                        "section_number": data.get("section_number"),
                    }
        except Exception:
            pass
    return meta_map

_METADATA_CACHE = None

def _enrich_chunk(chunk: dict) -> RetrievedChunk:
    global _METADATA_CACHE
    if _METADATA_CACHE is None:
        _METADATA_CACHE = _load_governance_metadata()
    
    title = chunk.get("title", "")
    meta = _METADATA_CACHE.get(title, {})
    
    # Priority: chunk's existing explicit metadata, then loaded file metadata, then safe defaults
    authority = chunk.get("authority_level") or meta.get("authority_level") or "UNKNOWN"
    jurisdiction = chunk.get("jurisdiction") or meta.get("jurisdiction") or "UNKNOWN"
    applicability = chunk.get("applicability") or meta.get("applicability") or ["UNKNOWN"]
    currentness = chunk.get("currentness_status") or meta.get("currentness_status") or "NEEDS_VERIFICATION"
    verification = chunk.get("verification_status") or meta.get("verification_status") or "NEEDS_VERIFICATION"
    precedence = chunk.get("precedence_tier") or meta.get("precedence_tier") or 10
    year = chunk.get("year") or meta.get("year")
    page_num = chunk.get("page_number") or meta.get("page_number")
    sec_num = chunk.get("section_number") or meta.get("section_number")

    return {
        "content": chunk.get("content", ""),
        "document_id": str(chunk.get("document_id", "")),
        "title": title,
        "source_name": chunk.get("source_name"),
        "source_url": chunk.get("source_url"),
        "document_type": chunk.get("document_type") or meta.get("document_type"),
        "language": chunk.get("language"),
        "similarity": float(chunk.get("similarity", 0.0)),
        "authority_level": authority,
        "jurisdiction": jurisdiction,
        "applicability": applicability,
        "currentness_status": currentness,
        "verification_status": verification,
        "precedence_tier": precedence,
        "year": year,
        "page_number": page_num,
        "section_number": sec_num,
    }

def _governance_sort_key(c: RetrievedChunk, query: str = "") -> tuple:
    """
    Governance sorting hierarchy strictly defined as:
    1. Jurisdiction & Applicability Match
    2. Currentness (ACTIVE_IN_FORCE -> AMENDED -> NEEDS_VERIFICATION -> UNKNOWN -> SUPERSEDED)
    3. Verification (VERIFIED_OFFICIAL -> OFFICIAL_NEEDS_VERIFICATION -> VERIFIED_EXPERT -> NEEDS_VERIFICATION -> REFERENCE_ONLY)
    4. Precedence Tier (Statutory Act -> Rules -> By-laws -> Schemes -> Advisories -> FAQs)
    5. Vector Similarity
    """
    q_lower = query.lower()

    # Jurisdiction match: if user mentions maharashtra, prioritize maharashtra
    juri = c.get("jurisdiction", "UNKNOWN")
    if "maharashtra" in q_lower or "महाराष्ट्र" in q_lower:
        juri_score = 0 if juri == "MAHARASHTRA" else (1 if juri == "INDIA" else 2)
    else:
        juri_score = 0 if juri in ["INDIA", "MAHARASHTRA"] else 1

    # Applicability score
    app_list = c.get("applicability") or []
    if any(w in q_lower for w in ["housing", "गृहनिर्माण"]):
        app_score = 0 if "HOUSING" in app_list else (1 if "ALL_COOPERATIVES" in app_list else 2)
    elif any(w in q_lower for w in ["pacs", "पैक्स", "पॅक्स"]):
        app_score = 0 if "PACS" in app_list else (1 if "ALL_COOPERATIVES" in app_list else 2)
    else:
        app_score = 0 if "ALL_COOPERATIVES" in app_list else 1

    # Currentness score
    curr_map = {
        "ACTIVE_IN_FORCE": 0,
        "AMENDED": 1,
        "NEEDS_VERIFICATION": 2,
        "UNKNOWN": 3,
        "SUPERSEDED": 4,
    }
    curr_score = curr_map.get(c.get("currentness_status") or "UNKNOWN", 3)

    # Verification score
    ver_map = {
        "VERIFIED_OFFICIAL": 0,
        "OFFICIAL_NEEDS_VERIFICATION": 1,
        "VERIFIED_EXPERT": 2,
        "NEEDS_VERIFICATION": 3,
        "REFERENCE_ONLY": 4,
    }
    ver_score = ver_map.get(c.get("verification_status") or "NEEDS_VERIFICATION", 3)

    prec = c.get("precedence_tier") or 10
    sim = c.get("similarity", 0.0)

    return (app_score, juri_score, curr_score, ver_score, -prec, -sim)


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
    Applies the 4-stage Governed Retrieval process:
    1. Intent & DocType pre-filtering
    2. Vector similarity retrieval (768-dim)
    3. Applicability isolation & safety filtering
    4. Multi-dimensional governance ranking
    """
    if not query or not query.strip():
        return []

    results = []

    # 1. Try Supabase pgvector search
    client = get_supabase_client()
    if client is not None:
        embedding_provider = GeminiEmbeddingProvider()
        query_vec = None
        try:
            query_vec = embedding_provider.embed_text(query)
            if query_vec and len(query_vec) == EMBEDDING_DIMENSION and any(v != 0.0 for v in query_vec):
                rpc_response = client.rpc(
                    "match_knowledge_chunks",
                    {
                        "query_embedding": query_vec,
                        "match_threshold": match_threshold,
                        "match_count": top_k * 3,  # fetch more for governance filtering
                        "filter_language": language,
                        "filter_intent": intent,
                    },
                ).execute()

                if rpc_response and rpc_response.data:
                    for item in rpc_response.data:
                        if not _is_doc_type_allowed(item.get("document_type"), intent):
                            continue
                        results.append(item)
                    
        except Exception as exc:
            logger.debug("Supabase RPC vector search unavailable: %s", exc)

        # 1b. Memory cache vector cosine similarity search if RPC yields 0 chunks
        if not results and query_vec and len(query_vec) == EMBEDDING_DIMENSION and any(v != 0.0 for v in query_vec):
            try:
                cached_chunks = _get_cached_chunks(client)
                scored = []
                for chunk in cached_chunks:
                    if not _is_doc_type_allowed(chunk.get("document_type"), intent):
                        continue
                    sim = _cosine_similarity(query_vec, chunk.get("embedding", []))
                    if sim >= match_threshold:
                        chunk_copy = chunk.copy()
                        chunk_copy["similarity"] = sim
                        scored.append(chunk_copy)
                scored.sort(key=lambda x: x["similarity"], reverse=True)
                results.extend(scored[:top_k * 3])
            except Exception as exc:
                logger.debug("Memory cache cosine similarity search error: %s", exc)

    # 2. Match local domain knowledge documents repository using exact word boundaries
    q_lower = query.lower().strip()
    for doc in LOCAL_KNOWLEDGE_DOCUMENTS:
        if not _is_doc_type_allowed(doc.get("document_type"), intent):
            continue

        matched = False
        for kw in doc.get("keywords", []):
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, q_lower):
                matched = True
                break

        if matched:
            doc_copy = doc.copy()
            doc_copy["similarity"] = 0.95
            results.append(doc_copy)

    # 3. Governance Enrichment
    enriched_results = []
    for item in results:
        enriched = _enrich_chunk(item)
        enriched_results.append(enriched)

    # 4. Strict Applicability & Domain Separation Filtering
    filtered_results = []
    for item in enriched_results:
        if _is_applicability_allowed(item, query):
            filtered_results.append(item)

    # Remove duplicates based on content
    unique_results = []
    seen_content = set()
    for item in filtered_results:
        if item["content"] not in seen_content:
            seen_content.add(item["content"])
            unique_results.append(item)

    # Sort based on governance rules with query context
    unique_results.sort(key=lambda c: _governance_sort_key(c, query))
    
    final_results = unique_results[:top_k]
    if final_results:
        logger.info("Retrieved %d governed domain knowledge chunks", len(final_results))
        
    return final_results
