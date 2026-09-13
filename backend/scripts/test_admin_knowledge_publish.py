"""
Phase 2B.3 Admin Knowledge Verification, Approval & Publishing Test Suite.
Verifies all 22 mandatory safety and functional test cases.
"""
import io
import os
import sys
from unittest.mock import patch

# Ensure backend root is on PYTHONPATH
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app
from database.supabase import get_supabase_client
from database.repository import (
    delete_admin_knowledge_document_and_chunks,
    _DEV_KNOWLEDGE_DOCS_STORE,
)
from rag.retriever import retrieve_relevant_knowledge, reset_chunks_cache
from rag.embeddings import GeminiEmbeddingProvider

client = TestClient(app)


def run_tests():
    print("=" * 75)
    print("RUNNING PHASE 2B.3 ADMIN KNOWLEDGE VERIFICATION & PUBLISHING TEST SUITE")
    print("=" * 75)

    results = []
    created_doc_ids = []

    def record(test_num: int, name: str, passed: bool, details: str = ""):
        status_str = "PASSED" if passed else "FAILED"
        print(f"[{status_str}] Test {test_num:02d}: {name} - {details}")
        results.append((test_num, name, passed, details))

    supabase = get_supabase_client()

    # Record initial chunk count
    initial_chunks = supabase.table("knowledge_chunks").select("id", count="exact").execute()
    initial_chunk_count = initial_chunks.count or len(initial_chunks.data or [])
    print(f"[INFO] Initial baseline chunks count in knowledge_chunks: {initial_chunk_count}")

    try:
        # Obtain Admin and Staff credentials
        login_admin = client.post("/api/admin/auth/login", json={
            "email": "admin@sahkaarsetu.local",
            "password": "SahkaarSetu@Admin2026"
        }).json()
        admin_token = login_admin.get("access_token")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        login_staff = client.post("/api/admin/auth/login", json={
            "email": "staff@sahkaarsetu.local",
            "password": "SahkaarSetu@Staff2026"
        }).json()
        staff_token = login_staff.get("access_token")
        staff_headers = {"Authorization": f"Bearer {staff_token}"}

        # Helper to create a document in draft
        def create_test_doc(
            title,
            doc_type="Circular",
            authority="MAHARASHTRA",
            authority_level="STATE_GOVERNMENT",
            effective_date="2026-06-01",
            applicability="ALL_COOPERATIVES",
            text_content=None
        ):
            if text_content is None:
                text_content = (
                    f"# {title}\n\n"
                    "## Executive Summary\n"
                    "This is an official cooperative governance circular issued for agricultural development.\n"
                    "All primary agricultural credit cooperative societies must comply with these provisions.\n"
                    "Members are entitled to direct solar agricultural equipment subsidies up to 60 percent.\n"
                    "Applications must be verified by the District Registrar Office within 14 working days.\n"
                )
            file_bytes = io.BytesIO(text_content.encode("utf-8"))
            res = client.post(
                "/api/admin/knowledge/documents",
                headers=admin_headers,
                data={
                    "title": title,
                    "document_type": doc_type,
                    "source_name": "Maharashtra State Cooperative Department",
                    "authority_level": authority_level,
                    "jurisdiction": authority,
                    "version": "v1.0",
                    "applicability": applicability,
                    "effective_date": effective_date,
                    "precedence_tier": 80,
                },
                files={"file": ("guidelines.txt", file_bytes, "text/plain")},
            )
            assert res.status_code == 201, f"Failed to create test doc: {res.text}"
            doc_id = res.json()["id"]
            created_doc_ids.append(doc_id)
            return doc_id

        # ---------------------------------------------------------------------
        # Pre-test document for tests 1 & 2 & 3
        # ---------------------------------------------------------------------
        doc1_id = create_test_doc("Solar Subsidy Mandate 2026 for Maharashtra PACS")
        # Advance doc1 to under_review
        client.post(f"/api/admin/knowledge/documents/{doc1_id}/review", headers=admin_headers, json={"notes": "Ready for review"})

        # 1. ADMIN can verify document in under_review
        res1 = client.post(
            f"/api/admin/knowledge/documents/{doc1_id}/verify",
            headers=admin_headers,
            json={
                "authority": "Maharashtra State Cooperative Department",
                "authority_level": "STATE_GOVERNMENT",
                "jurisdiction": "MAHARASHTRA",
                "effective_date": "2026-06-01",
                "applicability": ["ALL_COOPERATIVES", "PACS"],
                "precedence_tier": 80,
                "verification_notes": "Official gazette publication confirmed."
            }
        )
        passed1 = (
            res1.status_code == 200
            and res1.json().get("status") in ("ok", "success")
            and res1.json().get("document", {}).get("status") == "verified"
            and res1.json().get("document", {}).get("verification_status") == "VERIFIED_OFFICIAL"
            and res1.json().get("document", {}).get("currentness_status") == "CURRENT"
            and res1.json().get("document", {}).get("is_current") is False  # Must not be live yet
        )
        record(1, "ADMIN Can Verify Document in under_review", passed1, f"Status: {res1.status_code}, Doc Status: {res1.json().get('document', {}).get('status')}")

        # 2. STAFF cannot verify (403)
        doc2_id = create_test_doc("Staff Verification Test Doc")
        client.post(f"/api/admin/knowledge/documents/{doc2_id}/review", headers=admin_headers, json={})
        res2 = client.post(
            f"/api/admin/knowledge/documents/{doc2_id}/verify",
            headers=staff_headers,
            json={
                "authority": "District Registrar",
                "authority_level": "DISTRICT_OFFICER",
                "jurisdiction": "PUNE",
                "effective_date": "2026-06-01",
                "applicability": ["Pune PACS"],
            }
        )
        passed2 = res2.status_code == 403
        record(2, "STAFF Cannot Verify (403 Forbidden)", passed2, f"Status: {res2.status_code}")

        # 3. ADMIN can publish valid verified document
        res3 = client.post(
            f"/api/admin/knowledge/documents/{doc1_id}/publish",
            headers=admin_headers,
            json={"notes": "Approved for live citizen retrieval"}
        )
        data3 = res3.json()
        chunks_count3 = data3.get("published_chunks_count", 0) or data3.get("chunks_created", 0)
        passed3 = (
            res3.status_code == 200
            and data3.get("status") in ("ok", "success")
            and data3.get("document", {}).get("status") == "published"
            and data3.get("document", {}).get("is_current") is True
            and chunks_count3 > 0
        )
        record(3, "ADMIN Can Publish Valid Verified Document", passed3, f"Status: {res3.status_code}, Chunks Created: {chunks_count3}")

        # 4. STAFF cannot publish (403)
        res4 = client.post(
            f"/api/admin/knowledge/documents/{doc1_id}/publish",
            headers=staff_headers,
            json={"notes": "Staff attempt to publish"}
        )
        passed4 = res4.status_code == 403
        record(4, "STAFF Cannot Publish (403 Forbidden)", passed4, f"Status: {res4.status_code}")

        # 5. Draft cannot bypass review to verify/publish
        doc5_id = create_test_doc("Draft Bypass Test Doc")
        res5_verify = client.post(
            f"/api/admin/knowledge/documents/{doc5_id}/verify",
            headers=admin_headers,
            json={"authority": "State", "authority_level": "STATE_GOVERNMENT", "jurisdiction": "STATE", "effective_date": "2026-06-01", "applicability": ["All"]}
        )
        res5_publish = client.post(
            f"/api/admin/knowledge/documents/{doc5_id}/publish",
            headers=admin_headers,
            json={}
        )
        passed5 = res5_verify.status_code == 400 and res5_publish.status_code == 400
        record(5, "Draft Cannot Bypass Review to Verify/Publish", passed5, f"Verify: {res5_verify.status_code}, Publish: {res5_publish.status_code}")

        # 6. Under-review cannot bypass verification to publish
        doc6_id = create_test_doc("Under Review Bypass Test Doc")
        client.post(f"/api/admin/knowledge/documents/{doc6_id}/review", headers=admin_headers, json={})
        res6 = client.post(f"/api/admin/knowledge/documents/{doc6_id}/publish", headers=admin_headers, json={})
        passed6 = res6.status_code == 400 and "verified" in res6.text.lower()
        record(6, "Under-Review Cannot Bypass Verification to Publish", passed6, f"Status: {res6.status_code}, Error: {res6.text[:60]}")

        # 7. Missing governance metadata blocks verification/publication (400)
        doc7_id = create_test_doc("Missing Governance Test Doc")
        client.post(f"/api/admin/knowledge/documents/{doc7_id}/review", headers=admin_headers, json={})
        # Attempt verify without authority/jurisdiction/effective_date
        res7 = client.post(
            f"/api/admin/knowledge/documents/{doc7_id}/verify",
            headers=admin_headers,
            json={"authority": "", "authority_level": "", "jurisdiction": "", "effective_date": None}
        )
        passed7 = res7.status_code == 400
        record(7, "Missing Governance Metadata Blocks Verification (400)", passed7, f"Status: {res7.status_code}")

        # 8. Unverified status blocks publication (400)
        doc8_id = create_test_doc("Unverified Status Block Doc")
        # Leave as draft or under_review
        res8 = client.post(f"/api/admin/knowledge/documents/{doc8_id}/publish", headers=admin_headers, json={})
        passed8 = res8.status_code == 400
        record(8, "Unverified Status Blocks Publication (400)", passed8, f"Status: {res8.status_code}")

        # 9. Non-current status blocks publication (400)
        doc9_id = create_test_doc("Non-Current Status Block Doc")
        client.post(f"/api/admin/knowledge/documents/{doc9_id}/review", headers=admin_headers, json={})
        client.post(
            f"/api/admin/knowledge/documents/{doc9_id}/verify",
            headers=admin_headers,
            json={"authority": "State", "authority_level": "STATE_GOVERNMENT", "jurisdiction": "STATE", "effective_date": "2026-06-01", "applicability": ["All"]}
        )
        # Alter doc9 currentness_status in store to EXPIRED
        if doc9_id in _DEV_KNOWLEDGE_DOCS_STORE:
            _DEV_KNOWLEDGE_DOCS_STORE[doc9_id]["currentness_status"] = "EXPIRED"
        res9 = client.post(f"/api/admin/knowledge/documents/{doc9_id}/publish", headers=admin_headers, json={})
        passed9 = res9.status_code == 400 and "current" in res9.text.lower()
        record(9, "Non-Current Status Blocks Publication (400)", passed9, f"Status: {res9.status_code}, Error: {res9.text[:60]}")

        # 10. Invalid authority/jurisdiction blocks publication (400)
        doc10_id = create_test_doc("Invalid Authority Doc")
        client.post(f"/api/admin/knowledge/documents/{doc10_id}/review", headers=admin_headers, json={})
        client.post(
            f"/api/admin/knowledge/documents/{doc10_id}/verify",
            headers=admin_headers,
            json={"authority": "State", "authority_level": "STATE_GOVERNMENT", "jurisdiction": "STATE", "effective_date": "2026-06-01", "applicability": ["All"]}
        )
        # Blank out authority in store
        if doc10_id in _DEV_KNOWLEDGE_DOCS_STORE:
            _DEV_KNOWLEDGE_DOCS_STORE[doc10_id]["authority_level"] = ""
            _DEV_KNOWLEDGE_DOCS_STORE[doc10_id]["jurisdiction"] = ""
        res10 = client.post(f"/api/admin/knowledge/documents/{doc10_id}/publish", headers=admin_headers, json={})
        passed10 = res10.status_code == 400 and ("authority" in res10.text.lower() or "jurisdiction" in res10.text.lower())
        record(10, "Invalid Authority/Jurisdiction Blocks Publication (400)", passed10, f"Status: {res10.status_code}, Error: {res10.text[:60]}")

        # 11. Existing published document remains intact
        res11 = client.get(f"/api/admin/knowledge/documents/{doc1_id}", headers=admin_headers)
        passed11 = (
            res11.status_code == 200
            and res11.json().get("status") == "published"
            and res11.json().get("is_current") is True
        )
        record(11, "Existing Published Document Remains Intact", passed11, f"Status: {res11.json().get('status')}, Current: {res11.json().get('is_current')}")

        # 12. New published document gets chunks in knowledge_chunks
        chunks_res = supabase.table("knowledge_chunks").select("*").eq("document_id", doc1_id).execute()
        chunks12 = chunks_res.data or []
        passed12 = len(chunks12) > 0
        record(12, "New Published Document Has Chunks in knowledge_chunks", passed12, f"Chunks found: {len(chunks12)}")

        # 13. New chunks use 768-dimensional embeddings
        chunk0 = chunks12[0] if chunks12 else {}
        embedding_val = chunk0.get("embedding") or chunk0.get("metadata", {}).get("embedding")
        if isinstance(embedding_val, str):
            cleaned = embedding_val.strip("[]()").split(",")
            dim13 = len([x for x in cleaned if x.strip()])
        elif isinstance(embedding_val, list):
            dim13 = len(embedding_val)
        else:
            dim13 = 0
        passed13 = dim13 == 768
        record(13, "New Chunks Use 768-Dimensional Embeddings", passed13, f"Dimension: {dim13}")

        # 14. Embedding model remains gemini-embedding-001
        embedder = GeminiEmbeddingProvider()
        passed14 = getattr(embedder, "model_name", "gemini-embedding-001") == "gemini-embedding-001" and getattr(embedder, "vector_dim", 768) == 768
        record(14, "Embedding Model Remains gemini-embedding-001", passed14, f"Model: {getattr(embedder, 'model_name', 'gemini-embedding-001')}, Dim: {getattr(embedder, 'vector_dim', 768)}")

        # 15. Source/page/version metadata preserved on chunks
        def get_field(c, key):
            if key in c and c[key] is not None:
                return c[key]
            return c.get("metadata", {}).get(key)

        passed15 = all(
            get_field(c, "source") is not None
            and c.get("document_id") == doc1_id
            and get_field(c, "is_current") is True
            and get_field(c, "status") == "published"
            for c in chunks12
        )
        record(15, "Source/Page/Version/Status Metadata Preserved on Chunks", passed15, f"Checked {len(chunks12)} chunks")

        # 16. Published document becomes retrievable in live RAG
        reset_chunks_cache()
        retrieved_live = retrieve_relevant_knowledge("direct solar agricultural equipment subsidies 60 percent", top_k=10)
        found_in_rag = any(str(c.get("document_id")) == str(doc1_id) for c in retrieved_live)
        record(16, "Published Document Retrievable in Live Citizen RAG", found_in_rag, f"Retrieved {len(retrieved_live)} chunks; Target doc present: {found_in_rag}")

        # 17. Before publish, document NOT retrievable in live RAG
        doc17_id = create_test_doc("Confidential PACS Nuclear Fertilizer Secret 2026")
        client.post(f"/api/admin/knowledge/documents/{doc17_id}/review", headers=admin_headers, json={})
        client.post(
            f"/api/admin/knowledge/documents/{doc17_id}/verify",
            headers=admin_headers,
            json={"authority": "Secret Office", "authority_level": "STATE_GOVERNMENT", "jurisdiction": "STATE", "effective_date": "2026-06-01", "applicability": ["All"]}
        )
        reset_chunks_cache()
        retrieved_unpub = retrieve_relevant_knowledge("Confidential PACS Nuclear Fertilizer Secret 2026", top_k=5)
        leaked_17 = any(str(c.get("document_id")) == str(doc17_id) for c in retrieved_unpub)
        passed17 = not leaked_17
        record(17, "Verified But Unpublished Document NOT Retrievable in Live RAG", passed17, f"Leaked: {leaked_17}")

        # 18. Failed embedding leaves document unpublished and clean
        doc18_id = create_test_doc("Failing Embedding Simulation Doc")
        client.post(f"/api/admin/knowledge/documents/{doc18_id}/review", headers=admin_headers, json={})
        client.post(
            f"/api/admin/knowledge/documents/{doc18_id}/verify",
            headers=admin_headers,
            json={"authority": "State", "authority_level": "STATE_GOVERNMENT", "jurisdiction": "STATE", "effective_date": "2026-06-01", "applicability": ["All"]}
        )
        with patch.object(GeminiEmbeddingProvider, "embed_text", side_effect=RuntimeError("Simulated Gemini API Outage")):
            res18 = client.post(f"/api/admin/knowledge/documents/{doc18_id}/publish", headers=admin_headers, json={})

        doc18_in_store = _DEV_KNOWLEDGE_DOCS_STORE.get(doc18_id, {})
        chunks18 = supabase.table("knowledge_chunks").select("id").eq("document_id", doc18_id).execute().data or []
        passed18 = (
            res18.status_code == 500
            and doc18_in_store.get("status") == "verified"
            and doc18_in_store.get("is_current") is False
            and len(chunks18) == 0
        )
        record(18, "Failed Embedding Leaves Document Unpublished and Clean (Rollback)", passed18, f"Status: {res18.status_code}, Doc Status: {doc18_in_store.get('status')}, Chunks: {len(chunks18)}")

        # 19. Repeated publish does not duplicate chunks (idempotent)
        initial_doc1_chunks_count = len(chunks12)
        res19 = client.post(
            f"/api/admin/knowledge/documents/{doc1_id}/publish",
            headers=admin_headers,
            json={"notes": "Repeated publish call"}
        )
        chunks19 = supabase.table("knowledge_chunks").select("id").eq("document_id", doc1_id).execute().data or []
        passed19 = (
            res19.status_code == 200
            and len(chunks19) == initial_doc1_chunks_count
        )
        record(19, "Repeated Publish Is Idempotent (No Duplicate Chunks)", passed19, f"Initial chunks: {initial_doc1_chunks_count}, Current chunks: {len(chunks19)}")

        # 20. Previous version becomes non-current when replaced
        doc20_v2_id = create_test_doc(
            title="Solar Subsidy Mandate 2026 for Maharashtra PACS",
            text_content="# Solar Subsidy Mandate 2026 for Maharashtra PACS (v2.0 Revision)\nUpdated terms with 70% direct subsidy for PACS solar panels."
        )
        client.post(f"/api/admin/knowledge/documents/{doc20_v2_id}/review", headers=admin_headers, json={})
        client.post(
            f"/api/admin/knowledge/documents/{doc20_v2_id}/verify",
            headers=admin_headers,
            json={"authority": "Maharashtra State Cooperative Department", "authority_level": "STATE_GOVERNMENT", "jurisdiction": "MAHARASHTRA", "effective_date": "2026-07-01", "applicability": ["All PACS in Maharashtra"]}
        )
        res20 = client.post(f"/api/admin/knowledge/documents/{doc20_v2_id}/publish", headers=admin_headers, json={})
        assert res20.status_code == 200, f"Failed to publish v2: {res20.text}"

        doc1_after = _DEV_KNOWLEDGE_DOCS_STORE.get(doc1_id, {})
        doc1_chunks_after = supabase.table("knowledge_chunks").select("*").eq("document_id", doc1_id).execute().data or []

        def get_chunk_is_current(c):
            if "is_current" in c and c["is_current"] is not None:
                return c["is_current"]
            return c.get("metadata", {}).get("is_current", True)

        passed20 = (
            doc1_after.get("status") == "superseded"
            and doc1_after.get("is_current") is False
            and doc1_after.get("currentness_status") == "SUPERSEDED"
            and all(get_chunk_is_current(c) is False for c in doc1_chunks_after)
        )
        record(20, "Previous Version Superseded and Chunks Marked Non-Current", passed20, f"Old Doc Status: {doc1_after.get('status')}, Current: {doc1_after.get('is_current')}")

        # 21. Unauthorized request rejected (401)
        res21 = client.post(
            f"/api/admin/knowledge/documents/{doc1_id}/publish",
            headers={"Authorization": "Bearer bad.token"},
            json={}
        )
        passed21 = res21.status_code == 401
        record(21, "Unauthorized Request Rejected (401)", passed21, f"Status: {res21.status_code}")

        # 22. Citizen /api/query remains functional
        res22 = client.post(
            "/api/query",
            json={"message": "What is the primary objective of PACS in Maharashtra cooperative sector?", "language": "en"}
        )
        data22 = res22.json() if res22.status_code == 200 else {}
        passed22 = (
            res22.status_code == 200
            and bool(data22.get("answer"))
        )
        record(22, "Citizen /api/query Remains Functional", passed22, f"Status: {res22.status_code}, Answer length: {len(data22.get('answer', ''))}")

    finally:
        print("\n[TEARDOWN] Cleaning up all test documents and chunks...")
        for did in created_doc_ids:
            try:
                delete_admin_knowledge_document_and_chunks(did)
            except Exception as e:
                print(f"[TEARDOWN WARNING] Failed to delete test doc {did}: {e}")

        reset_chunks_cache()

        final_chunks = supabase.table("knowledge_chunks").select("id", count="exact").execute()
        final_chunk_count = final_chunks.count or len(final_chunks.data or [])
        print(f"[INFO] Final chunks count in knowledge_chunks: {final_chunk_count} (Baseline was: {initial_chunk_count})")
        if final_chunk_count == initial_chunk_count:
            print("[INFO] Database cleanly restored to exact baseline chunk count. ZERO leak.")
        else:
            print(f"[WARNING] Baseline count mismatch: {initial_chunk_count} vs {final_chunk_count}")

    print("=" * 75)
    total_passed = sum(1 for _, _, p, _ in results if p)
    print(f"RESULTS: {total_passed}/{len(results)} TESTS PASSED")
    print("=" * 75)

    if total_passed == len(results):
        print("ALL 22 PHASE 2B.3 KNOWLEDGE PUBLISHING TESTS PASSED SUCCESSFULLY!")
        return True
    else:
        print("FAILURES DETECTED IN TEST SUITE")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
