"""
Phase 2B.1 Governed Knowledge Safety Gate Test Suite.
Verifies the 15 mandatory safety and regression test cases.
"""
import os
import sys

# Ensure backend root is on PYTHONPATH
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app
from rag.retriever import retrieve_relevant_knowledge
from rag.embeddings import EMBEDDING_DIMENSION, DEFAULT_EMBEDDING_MODEL
from database.repository import (
    get_knowledge_documents,
    set_document_governance_overlay,
    clear_document_governance_overlay,
)
from database.supabase import get_supabase_client

client = TestClient(app)


def run_tests():
    print("=" * 70)
    print("RUNNING PHASE 2B.1 GOVERNED KNOWLEDGE SAFETY GATE TEST SUITE")
    print("=" * 70)

    results = []

    def record(test_num: int, name: str, passed: bool, details: str = ""):
        status_str = "PASSED" if passed else "FAILED"
        print(f"[{status_str}] Test {test_num:02d}: {name} - {details}")
        results.append((test_num, name, passed, details))

    # Clean any previous test overlays
    clear_document_governance_overlay()

    # 1. Published + current document is retrievable
    chunks_pacs = retrieve_relevant_knowledge("What is PACS Primary Agricultural Credit Society?", top_k=3)
    passed = len(chunks_pacs) > 0 and all(
        (c.get("status") or "published") == "published" and c.get("is_current", True) is True
        for c in chunks_pacs
    )
    record(1, "Published & Current Document Retrievable", passed, f"Retrieved: {len(chunks_pacs)} chunks")

    # 2. Draft document is NOT retrievable
    # Set one of the active documents to 'draft' in test overlay
    target_doc_id = "430c34f0-a053-4cad-be13-bf5f8bdd9ec8"  # PACS Overview
    set_document_governance_overlay(target_doc_id, {"status": "draft", "is_current": True})
    chunks_draft_test = retrieve_relevant_knowledge("Primary Agricultural Credit Societies (PACS) Governance", top_k=5)
    leaked_draft = [c for c in chunks_draft_test if str(c.get("document_id")) == target_doc_id]
    passed = len(leaked_draft) == 0
    record(2, "Draft Document Strictly Excluded", passed, f"Leaked draft count: {len(leaked_draft)}")

    # 3. Under-review document is NOT retrievable
    set_document_governance_overlay(target_doc_id, {"status": "under_review", "is_current": True})
    chunks_review_test = retrieve_relevant_knowledge("Primary Agricultural Credit Societies (PACS) Governance", top_k=5)
    leaked_review = [c for c in chunks_review_test if str(c.get("document_id")) == target_doc_id]
    passed = len(leaked_review) == 0
    record(3, "Under-Review Document Strictly Excluded", passed, f"Leaked under_review count: {len(leaked_review)}")

    # 4. Verified but unpublished document is NOT retrievable
    set_document_governance_overlay(target_doc_id, {"status": "verified", "is_current": True})
    chunks_verified_test = retrieve_relevant_knowledge("Primary Agricultural Credit Societies (PACS) Governance", top_k=5)
    leaked_verified = [c for c in chunks_verified_test if str(c.get("document_id")) == target_doc_id]
    passed = len(leaked_verified) == 0
    record(4, "Verified (Unpublished) Document Strictly Excluded", passed, f"Leaked verified count: {len(leaked_verified)}")

    # 5. Published but non-current document is NOT retrievable
    set_document_governance_overlay(target_doc_id, {"status": "published", "is_current": False})
    chunks_noncurrent_test = retrieve_relevant_knowledge("Primary Agricultural Credit Societies (PACS) Governance", top_k=5)
    leaked_noncurrent = [c for c in chunks_noncurrent_test if str(c.get("document_id")) == target_doc_id]
    passed = len(leaked_noncurrent) == 0
    record(5, "Published Non-Current Document Strictly Excluded", passed, f"Leaked non-current count: {len(leaked_noncurrent)}")

    # 6. Superseded document is NOT retrievable
    set_document_governance_overlay(target_doc_id, {"status": "superseded", "is_current": False})
    chunks_superseded_test = retrieve_relevant_knowledge("Primary Agricultural Credit Societies (PACS) Governance", top_k=5)
    leaked_superseded = [c for c in chunks_superseded_test if str(c.get("document_id")) == target_doc_id]
    passed = len(leaked_superseded) == 0
    record(6, "Superseded Document Strictly Excluded", passed, f"Leaked superseded count: {len(leaked_superseded)}")

    # Restore target document to published + current
    clear_document_governance_overlay()

    # 7. Published/current document remains retrievable after restore
    chunks_restored = retrieve_relevant_knowledge("Primary Agricultural Credit Societies (PACS) Governance", top_k=5)
    passed = len(chunks_restored) > 0 and any(str(c.get("document_id")) == target_doc_id for c in chunks_restored)
    record(7, "Restored Published Document Retrievable", passed, f"Found target: {passed}")

    # 8. Housing document cannot answer PACS query when applicability rules reject it
    chunks_pacs_app = retrieve_relevant_knowledge("How do PACS credit societies disburse crop loans to farmers?", top_k=4)
    housing_chunks = [c for c in chunks_pacs_app if "housing" in c.get("title", "").lower() or "HOUSING" in (c.get("applicability") or [])]
    passed = len(housing_chunks) == 0
    record(8, "Applicability Isolation (No Housing Chunks for PACS)", passed, f"Housing chunks in PACS query: {len(housing_chunks)}")

    # 9. Jurisdiction filtering still works
    chunks_mh = retrieve_relevant_knowledge("Maharashtra cooperative societies audit section 81", intent="COOPERATIVE_LAW", top_k=3)
    passed = len(chunks_mh) > 0 and chunks_mh[0].get("jurisdiction") == "MAHARASHTRA"
    record(9, "Jurisdiction Filtering (Maharashtra Preferred)", passed, f"Top jurisdiction: {chunks_mh[0].get('jurisdiction') if chunks_mh else 'None'}")

    # 10. Existing governance ranking still works (Statutory Act precedence >= 90)
    top_chunk = chunks_mh[0] if chunks_mh else {}
    passed = (top_chunk.get("precedence_tier") or 0) >= 90
    record(10, "Governance Precedence Ranking (Tier 1 Statutory Act)", passed, f"Top tier: {top_chunk.get('precedence_tier')}")

    # 11. Source traceability remains intact
    all_traceable = all(
        c.get("document_id") and c.get("title") and c.get("source_name") and c.get("source_url")
        for c in chunks_mh
    )
    record(11, "Source Traceability (Doc ID, Title, Source Name, URL)", all_traceable, f"Traceable chunks: {len(chunks_mh)}")

    # 12. No chunk count is unexpectedly lost (Verify 29 chunks, 8 docs)
    sb_client = get_supabase_client()
    docs_db = sb_client.table("knowledge_documents").select("id").execute().data or []
    chunks_db = sb_client.table("knowledge_chunks").select("id").execute().data or []
    passed = len(docs_db) >= 8 and len(chunks_db) == 29
    record(12, "Corpus Integrity Preservation", passed, f"Docs in DB: {len(docs_db)}, Chunks in DB: {len(chunks_db)}")

    # 13. Embedding dimension remains 768
    passed = EMBEDDING_DIMENSION == 768
    record(13, "Vector Embedding Dimension Invariant", passed, f"Dimension: {EMBEDDING_DIMENSION}")

    # 14. Embedding model remains gemini-embedding-001
    passed = DEFAULT_EMBEDDING_MODEL == "gemini-embedding-001"
    record(14, "Gemini Embedding Model Invariant", passed, f"Model: {DEFAULT_EMBEDDING_MODEL}")

    # 15. Existing citizen /api/query remains functional
    res_query = client.post("/api/query", json={
        "message": "What is PACS?",
        "session_id": "test-session-safety-gate",
        "language": "en"
    })
    passed = res_query.status_code == 200 and "answer" in res_query.json()
    record(15, "Citizen /api/query RAG Compatibility", passed, f"Status: {res_query.status_code}")

    print("=" * 70)
    all_passed = all(r[2] for r in results)
    pass_count = sum(1 for r in results if r[2])
    print(f"RESULTS: {pass_count}/{len(results)} TESTS PASSED")
    if all_passed:
        print("ALL GOVERNED KNOWLEDGE SAFETY TESTS PASSED.")
    else:
        print("SOME TESTS FAILED.")
    print("=" * 70)

    # Clean up overlay
    clear_document_governance_overlay()
    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
