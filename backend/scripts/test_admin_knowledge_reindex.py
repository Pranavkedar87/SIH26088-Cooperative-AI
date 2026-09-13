"""
Phase 2B.4 Admin Knowledge Version Management & Safe Re-indexing Test Suite.
Verifies all 22 mandatory safety, versioning, authorization, failure handling, and functional test cases.
"""
import io
import os
import sys
import uuid
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
from rag.embeddings import GeminiEmbeddingProvider, EMBEDDING_DIMENSION

client = TestClient(app)


def run_tests():
    print("=" * 75)
    print("RUNNING PHASE 2B.4 ADMIN KNOWLEDGE VERSION & REINDEX TEST SUITE")
    print("=" * 75)

    results = []
    created_doc_ids = []

    def record(test_num: int, name: str, passed: bool, details: str = ""):
        status_str = "PASSED" if passed else "FAILED"
        print(f"[{status_str}] Test {test_num:02d}: {name} - {details}")
        results.append((test_num, name, passed, details))

    supabase = get_supabase_client()

    # Record initial baseline chunk count
    initial_chunks = supabase.table("knowledge_chunks").select("id", count="exact").execute()
    initial_chunk_count = initial_chunks.count or len(initial_chunks.data or [])
    print(f"[INFO] Initial baseline chunks count in knowledge_chunks: {initial_chunk_count}")

    # Helper to clean up documents created in tests
    def cleanup_doc(doc_id):
        try:
            delete_admin_knowledge_document_and_chunks(doc_id)
        except Exception as exc:
            print(f"[WARN] Failed to clean up doc {doc_id}: {exc}")

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

        # Mock embedding provider for fast and deterministic test execution
        mock_vec = [0.05] * EMBEDDING_DIMENSION

        def create_and_publish_test_doc(title, version="v1.0", text_content=None):
            if text_content is None:
                text_content = (
                    f"# {title}\n\n"
                    "## Executive Guidance\n"
                    "This is an official cooperative governance circular for agricultural societies.\n"
                    "All primary agricultural credit societies must follow these solar irrigation guidelines.\n"
                    "Subsidies are capped at 75 percent for smallholder farming communities.\n"
                )
            file_bytes = io.BytesIO(text_content.encode("utf-8"))
            # 1. Upload as draft
            res_up = client.post(
                "/api/admin/knowledge/documents",
                headers=admin_headers,
                data={
                    "title": title,
                    "document_type": "Circular",
                    "source_name": "Maharashtra State Cooperative Department",
                    "authority_level": "STATE_GOVERNMENT",
                    "jurisdiction": "MAHARASHTRA",
                    "version": version,
                    "applicability": "ALL_COOPERATIVES",
                    "effective_date": "2026-06-01",
                    "precedence_tier": 80,
                },
                files={"file": ("guidelines.txt", file_bytes, "text/plain")},
            )
            doc_id = res_up.json()["id"]
            created_doc_ids.append(doc_id)

            # 2. Transition to under_review
            client.post(f"/api/admin/knowledge/documents/{doc_id}/review", headers=admin_headers)

            # 3. Verify
            client.post(f"/api/admin/knowledge/documents/{doc_id}/verify", headers=admin_headers, json={
                "authority_level": "STATE_GOVERNMENT",
                "jurisdiction": "MAHARASHTRA",
                "applicability": ["ALL_COOPERATIVES"],
                "effective_date": "2026-06-01",
                "precedence_tier": 80,
                "verification_notes": "Verified official",
            })

            # 4. Publish with mocked embeddings
            with patch.object(GeminiEmbeddingProvider, "embed_text", return_value=mock_vec):
                res_pub = client.post(f"/api/admin/knowledge/documents/{doc_id}/publish", headers=admin_headers)
                assert res_pub.status_code == 200, f"Failed publishing doc: {res_pub.text}"

            return doc_id

        # Setup standard test doc
        base_title = f"PACS Solar Irrigation Guidelines 2026 {uuid.uuid4().hex[:6]}"
        published_doc_id = create_and_publish_test_doc(base_title, version="v1.0")

        # -------------------------------------------------------------
        # Test 1: Version History retrieval for valid document returns 200 OK
        # -------------------------------------------------------------
        res_v1 = client.get(f"/api/admin/knowledge/documents/{published_doc_id}/versions", headers=admin_headers)
        data_v1 = res_v1.json()
        passed_1 = (
            res_v1.status_code == 200
            and data_v1.get("status") == "ok"
            and data_v1.get("document_id") == published_doc_id
            and data_v1.get("lineage_title") == base_title
            and data_v1.get("current_version") == "v1.0"
            and len(data_v1.get("versions", [])) >= 1
        )
        record(1, "GET /versions returns 200 OK and valid lineage structure", passed_1, f"total={data_v1.get('total_versions')}")

        # -------------------------------------------------------------
        # Test 2: Version History returns 404 for non-existent document
        # -------------------------------------------------------------
        res_v2 = client.get(f"/api/admin/knowledge/documents/{uuid.uuid4()}/versions", headers=admin_headers)
        record(2, "GET /versions returns 404 for non-existent doc ID", res_v2.status_code == 404, f"status={res_v2.status_code}")

        # -------------------------------------------------------------
        # Test 3: Version History accessible by authenticated STAFF operator
        # -------------------------------------------------------------
        res_v3 = client.get(f"/api/admin/knowledge/documents/{published_doc_id}/versions", headers=staff_headers)
        record(3, "GET /versions accessible to authenticated STAFF operator (200 OK)", res_v3.status_code == 200, f"status={res_v3.status_code}")

        # -------------------------------------------------------------
        # Test 4: Version History rejects unauthenticated request with 401
        # -------------------------------------------------------------
        res_v4 = client.get(f"/api/admin/knowledge/documents/{published_doc_id}/versions")
        record(4, "GET /versions rejects unauthenticated request with 401", res_v4.status_code == 401, f"status={res_v4.status_code}")

        # -------------------------------------------------------------
        # Test 5: Re-index rejects unauthenticated request with 401
        # -------------------------------------------------------------
        res_r5 = client.post(f"/api/admin/knowledge/documents/{published_doc_id}/reindex")
        record(5, "POST /reindex rejects unauthenticated request with 401", res_r5.status_code == 401, f"status={res_r5.status_code}")

        # -------------------------------------------------------------
        # Test 6: Re-index rejects STAFF operator with 403 Forbidden
        # -------------------------------------------------------------
        res_r6 = client.post(f"/api/admin/knowledge/documents/{published_doc_id}/reindex", headers=staff_headers)
        record(6, "POST /reindex rejects STAFF operator with 403 Forbidden", res_r6.status_code == 403, f"status={res_r6.status_code}")

        # -------------------------------------------------------------
        # Test 7: Re-index returns 404 for non-existent document
        # -------------------------------------------------------------
        res_r7 = client.post(f"/api/admin/knowledge/documents/{uuid.uuid4()}/reindex", headers=admin_headers)
        record(7, "POST /reindex returns 404 for non-existent doc ID", res_r7.status_code == 404, f"status={res_r7.status_code}")

        # -------------------------------------------------------------
        # Test 8: Re-index rejects DRAFT document with 400 Bad Request
        # -------------------------------------------------------------
        file_bytes = io.BytesIO(b"# Draft Doc\nSome draft content here.")
        res_draft = client.post(
            "/api/admin/knowledge/documents",
            headers=admin_headers,
            data={"title": "Draft Unapproved Doc", "document_type": "Circular"},
            files={"file": ("draft.txt", file_bytes, "text/plain")},
        )
        draft_doc_id = res_draft.json()["id"]
        created_doc_ids.append(draft_doc_id)

        res_r8 = client.post(f"/api/admin/knowledge/documents/{draft_doc_id}/reindex", headers=admin_headers)
        record(8, "POST /reindex rejects DRAFT document with 400 Bad Request", res_r8.status_code == 400, f"detail={res_r8.json().get('detail')}")

        # -------------------------------------------------------------
        # Test 9: Re-index rejects UNDER_REVIEW document with 400 Bad Request
        # -------------------------------------------------------------
        client.post(f"/api/admin/knowledge/documents/{draft_doc_id}/review", headers=admin_headers)
        res_r9 = client.post(f"/api/admin/knowledge/documents/{draft_doc_id}/reindex", headers=admin_headers)
        record(9, "POST /reindex rejects UNDER_REVIEW document with 400 Bad Request", res_r9.status_code == 400, f"detail={res_r9.json().get('detail')}")

        # -------------------------------------------------------------
        # Test 10: Re-index rejects VERIFIED document with 400 Bad Request (must be published first)
        # -------------------------------------------------------------
        client.post(f"/api/admin/knowledge/documents/{draft_doc_id}/verify", headers=admin_headers, json={
            "authority_level": "STATE_GOVERNMENT",
            "jurisdiction": "MAHARASHTRA",
            "applicability": ["ALL_COOPERATIVES"],
            "effective_date": "2026-06-01",
            "precedence_tier": 50,
            "verification_notes": "Verified",
        })
        res_r10 = client.post(f"/api/admin/knowledge/documents/{draft_doc_id}/reindex", headers=admin_headers)
        record(10, "POST /reindex rejects VERIFIED (unpublished) doc with 400 Bad Request", res_r10.status_code == 400, f"detail={res_r10.json().get('detail')}")

        # -------------------------------------------------------------
        # Test 11: Setup second version of lineage to test superseded status rejection
        # -------------------------------------------------------------
        v2_doc_id = create_and_publish_test_doc(base_title, version="v2.0", text_content=(
            f"# {base_title} Version 2\n\n"
            "## Updated Guidelines\n"
            "This circular supersedes all previous solar equipment subsidy norms.\n"
            "The updated subsidy cap is 80 percent for tribal area cooperatives.\n"
        ))
        # Now published_doc_id (v1.0) is superseded!
        res_r11 = client.post(f"/api/admin/knowledge/documents/{published_doc_id}/reindex", headers=admin_headers)
        record(11, "POST /reindex rejects SUPERSEDED document with 400 Bad Request", res_r11.status_code == 400, f"detail={res_r11.json().get('detail')}")

        # -------------------------------------------------------------
        # Test 12: Re-index rejects non-current document with 400 Bad Request
        # -------------------------------------------------------------
        doc_v1_rec = _DEV_KNOWLEDGE_DOCS_STORE.get(published_doc_id, {})
        passed_12 = (res_r11.status_code == 400 and doc_v1_rec.get("is_current") is False)
        record(12, "POST /reindex enforces is_current=True requirement (400 if is_current=False)", passed_12, f"is_current={doc_v1_rec.get('is_current')}")

        # -------------------------------------------------------------
        # Test 13: Safe Re-index succeeds for valid PUBLISHED and CURRENT document
        # -------------------------------------------------------------
        with patch.object(GeminiEmbeddingProvider, "embed_text", return_value=mock_vec):
            res_r13 = client.post(
                f"/api/admin/knowledge/documents/{v2_doc_id}/reindex",
                headers=admin_headers,
                json={"notes": "Routine index refresh"}
            )
        data_r13 = res_r13.json()
        passed_13 = (
            res_r13.status_code == 200
            and data_r13.get("status") == "ok"
            and data_r13.get("document_id") == v2_doc_id
            and data_r13.get("chunks_created", 0) > 0
        )
        record(13, "Safe Re-index succeeds for valid PUBLISHED and CURRENT doc (200 OK)", passed_13, f"chunks={data_r13.get('chunks_created')}")

        # -------------------------------------------------------------
        # Test 14: Re-index response confirms embedding model is gemini-embedding-001 and dimension 768
        # -------------------------------------------------------------
        passed_14 = (
            data_r13.get("embedding_model") == "gemini-embedding-001"
            and data_r13.get("embedding_dimension") == 768
            and "reindexed_at" in data_r13
        )
        record(14, "Re-index confirms embedding_model='gemini-embedding-001' and dimension=768", passed_14, f"dim={data_r13.get('embedding_dimension')}")

        # -------------------------------------------------------------
        # Test 15: Re-index keeps document in published and current state
        # -------------------------------------------------------------
        doc_v2_rec = _DEV_KNOWLEDGE_DOCS_STORE.get(v2_doc_id, {})
        passed_15 = (
            doc_v2_rec.get("status") == "published"
            and doc_v2_rec.get("is_current") is True
            and data_r13.get("is_current") is True
        )
        record(15, "Re-index preserves document status='published' and is_current=True", passed_15, f"status={doc_v2_rec.get('status')}")

        # -------------------------------------------------------------
        # Test 16: Duplicate prevention: chunk count does not multiply or leave duplicate stale chunks
        # -------------------------------------------------------------
        chunks_res_1 = supabase.table("knowledge_chunks").select("id", count="exact").eq("document_id", v2_doc_id).execute()
        count_first = chunks_res_1.count or len(chunks_res_1.data or [])

        # Re-index again
        with patch.object(GeminiEmbeddingProvider, "embed_text", return_value=mock_vec):
            res_r16 = client.post(f"/api/admin/knowledge/documents/{v2_doc_id}/reindex", headers=admin_headers)
        assert res_r16.status_code == 200

        chunks_res_2 = supabase.table("knowledge_chunks").select("id", count="exact").eq("document_id", v2_doc_id).execute()
        count_second = chunks_res_2.count or len(chunks_res_2.data or [])
        passed_16 = (count_first == count_second and count_first > 0)
        record(16, "Duplicate prevention: re-indexing replaces chunks cleanly without accumulation", passed_16, f"count1={count_first}, count2={count_second}")

        # -------------------------------------------------------------
        # Test 17: Failure safety: if source file cannot be read, chunks remain intact
        # -------------------------------------------------------------
        before_chunks = supabase.table("knowledge_chunks").select("id", count="exact").eq("document_id", v2_doc_id).execute()
        before_count = before_chunks.count or len(before_chunks.data or [])

        with patch("database.storage.read_knowledge_file", return_value=None):
            res_fail_file = client.post(f"/api/admin/knowledge/documents/{v2_doc_id}/reindex", headers=admin_headers)

        after_chunks = supabase.table("knowledge_chunks").select("id", count="exact").eq("document_id", v2_doc_id).execute()
        after_count = after_chunks.count or len(after_chunks.data or [])

        passed_17 = (res_fail_file.status_code == 400 and before_count == after_count and before_count > 0)
        record(17, "Failure safety: unreadable source file blocks re-index, existing chunks remain intact", passed_17, f"status={res_fail_file.status_code}, chunks={after_count}")

        # -------------------------------------------------------------
        # Test 18: Failure safety: if Gemini embedding provider raises exception, chunks remain intact
        # -------------------------------------------------------------
        with patch.object(GeminiEmbeddingProvider, "embed_text", side_effect=RuntimeError("Simulated Gemini API Outage")):
            res_fail_gemini = client.post(f"/api/admin/knowledge/documents/{v2_doc_id}/reindex", headers=admin_headers)

        after_chunks_18 = supabase.table("knowledge_chunks").select("id", count="exact").eq("document_id", v2_doc_id).execute()
        after_count_18 = after_chunks_18.count or len(after_chunks_18.data or [])

        passed_18 = (res_fail_gemini.status_code == 500 and before_count == after_count_18)
        record(18, "Failure safety: Gemini API outage returns 500, existing chunks remain 100% untouched", passed_18, f"status={res_fail_gemini.status_code}, chunks={after_count_18}")

        # -------------------------------------------------------------
        # Test 19: Failure safety: if embedding dimension is invalid (not 768), chunks remain intact
        # -------------------------------------------------------------
        invalid_dim_vec = [0.1] * 512  # Invalid 512-dim vector instead of 768
        with patch.object(GeminiEmbeddingProvider, "embed_text", return_value=invalid_dim_vec):
            res_fail_dim = client.post(f"/api/admin/knowledge/documents/{v2_doc_id}/reindex", headers=admin_headers)

        after_chunks_19 = supabase.table("knowledge_chunks").select("id", count="exact").eq("document_id", v2_doc_id).execute()
        after_count_19 = after_chunks_19.count or len(after_chunks_19.data or [])

        passed_19 = (res_fail_dim.status_code == 500 and before_count == after_count_19)
        record(19, "Failure safety: non-768 dimension rejected with 500, existing chunks untouched", passed_19, f"status={res_fail_dim.status_code}, chunks={after_count_19}")

        # -------------------------------------------------------------
        # Test 20: Version lineage reflects multiple versions and correctly marks CURRENT vs SUPERSEDED
        # -------------------------------------------------------------
        res_lineage = client.get(f"/api/admin/knowledge/documents/{v2_doc_id}/versions", headers=admin_headers)
        lineage_data = res_lineage.json()
        versions = lineage_data.get("versions", [])
        v1_item = next((v for v in versions if v["id"] == published_doc_id), None)
        v2_item = next((v for v in versions if v["id"] == v2_doc_id), None)

        passed_20 = (
            res_lineage.status_code == 200
            and len(versions) >= 2
            and lineage_data.get("current_version") == "v2.0"
            and v1_item is not None
            and v1_item.get("status") == "superseded"
            and v1_item.get("is_current") is False
            and v2_item is not None
            and v2_item.get("status") == "published"
            and v2_item.get("is_current") is True
        )
        record(20, "Version lineage correctly tracks multiple versions (v1 superseded, v2 current)", passed_20, f"current_ver={lineage_data.get('current_version')}")

        # -------------------------------------------------------------
        # Test 21: Citizen live RAG retrieval excludes superseded versions
        # -------------------------------------------------------------
        reset_chunks_cache()
        rag_chunks = retrieve_relevant_knowledge("tribal area cooperatives solar equipment subsidy", language="en", top_k=5)
        superseded_in_rag = any(c.get("document_id") == published_doc_id for c in rag_chunks)
        record(21, "Citizen live RAG excludes superseded document chunks from retrieval", not superseded_in_rag, f"rag_chunks={len(rag_chunks)}")

        # -------------------------------------------------------------
        # Test 22: Teardown & Clean Corpus Verification
        # -------------------------------------------------------------
        print("\n[INFO] Tearing down all test documents and verifying corpus baseline...")
        for did in created_doc_ids:
            cleanup_doc(did)

        reset_chunks_cache()
        final_chunks = supabase.table("knowledge_chunks").select("id", count="exact").execute()
        final_chunk_count = final_chunks.count or len(final_chunks.data or [])

        passed_22 = (final_chunk_count == initial_chunk_count)
        record(22, "Corpus Integrity: All test chunks deleted, baseline count exactly preserved", passed_22, f"initial={initial_chunk_count}, final={final_chunk_count}")

    except Exception as exc:
        import traceback
        print(f"\n[FATAL] Exception in test execution: {exc}")
        traceback.print_exc()
        for did in created_doc_ids:
            cleanup_doc(did)

    print("\n" + "=" * 75)
    print("PHASE 2B.4 TEST SUMMARY")
    print("=" * 75)
    total_tests = len(results)
    passed_tests = sum(1 for _, _, p, _ in results if p)
    print(f"Total Tests : {total_tests}")
    print(f"Passed      : {passed_tests}")
    print(f"Failed      : {total_tests - passed_tests}")
    print("=" * 75)

    if passed_tests == total_tests and total_tests == 22:
        print("\nPASS — VERSION MANAGEMENT AND REINDEX VERIFIED\n")
        return 0
    else:
        print("\nBLOCKED — VERSION/REINDEX SAFETY NOT VERIFIED\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
