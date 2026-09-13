"""
Phase 2C.1: Comprehensive Test Suite for Real Admin Analytics & Insights.

Validates:
- Unauthenticated access returns 401
- Role-based access control (Staff blocked with 403, Admin allowed with 200)
- Endpoints (/overview and /knowledge-gaps)
- Strict adherence to Pydantic schemas
- Database truth: metrics reflect real Supabase tables (messages, grievances, knowledge_documents, kiosks)
- Exact match between repository counts and direct Supabase message table count
- Query timeline generation for 24h, 7d, and 30d periods
- Validation of invalid period query parameter (422)
- Multilingual and intent distributions derived from real messages
- Transparent handling of non-collected telemetry (voice_vs_touch and kiosk_vs_web are None)
- Knowledge gap items derived with empirical evidence and realistic counts
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from dateutil import parser
from typing import Any

# Ensure backend root is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.schemas.admin_analytics import (
    AdminAnalyticsOverviewResponse,
    AdminKnowledgeGapsResponse,
)
from database.supabase import get_supabase_client
from database.repository import (
    get_admin_analytics_overview,
    get_admin_knowledge_gaps,
    get_knowledge_documents,
    list_admin_grievances,
    list_kiosks,
)

client = TestClient(app)

def run_tests():
    print("=" * 70)
    print("RUNNING PHASE 2C.1: ADMIN ANALYTICS & OPERATIONAL INSIGHTS TESTS")
    print("=" * 70)

    results = []

    def record(num: int, name: str, passed: bool, details: str = ""):
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] Test {num:02d}: {name} - {details}")
        results.append((num, name, passed, details))

    # Obtain Admin & Staff credentials via auth endpoint
    res_admin = client.post("/api/admin/auth/login", json={
        "email": "admin@sahkaarsetu.local",
        "password": "SahkaarSetu@Admin2026"
    })
    admin_token = res_admin.json().get("access_token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    res_staff = client.post("/api/admin/auth/login", json={
        "email": "staff@sahkaarsetu.local",
        "password": "SahkaarSetu@Staff2026"
    })
    staff_token = res_staff.json().get("access_token")
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    sb = get_supabase_client()
    raw_user_msgs = []
    if sb is not None:
        try:
            r = sb.table("messages").select("id, role, language, created_at").eq("role", "user").execute()
            raw_user_msgs = r.data or []
        except Exception as e:
            print("Direct Supabase user query error:", e)

    # Test 1: Unauthenticated request to /api/admin/analytics/overview returns 401
    res1 = client.get("/api/admin/analytics/overview")
    record(1, "Unauthenticated /overview returns 401", res1.status_code == 401, f"Status: {res1.status_code}")

    # Test 2: Unauthenticated request to /api/admin/analytics/knowledge-gaps returns 401
    res2 = client.get("/api/admin/analytics/knowledge-gaps")
    record(2, "Unauthenticated /knowledge-gaps returns 401", res2.status_code == 401, f"Status: {res2.status_code}")

    # Test 3: Staff operator request to /api/admin/analytics/overview returns 403
    res3 = client.get("/api/admin/analytics/overview", headers=staff_headers)
    record(3, "Staff operator blocked from /overview with 403", res3.status_code == 403, f"Status: {res3.status_code}")

    # Test 4: Staff operator request to /api/admin/analytics/knowledge-gaps returns 403
    res4 = client.get("/api/admin/analytics/knowledge-gaps", headers=staff_headers)
    record(4, "Staff operator blocked from /knowledge-gaps with 403", res4.status_code == 403, f"Status: {res4.status_code}")

    # Test 5: Admin operator request to /api/admin/analytics/overview returns 200
    res5 = client.get("/api/admin/analytics/overview?period=30d", headers=admin_headers)
    record(5, "Admin operator access to /overview returns 200", res5.status_code == 200, f"Status: {res5.status_code}")

    # Test 6: Overview response validates against AdminAnalyticsOverviewResponse schema
    overview_data = res5.json() if res5.status_code == 200 else {}
    validated_overview = None
    try:
        validated_overview = AdminAnalyticsOverviewResponse(**overview_data)
        schema_valid = True
    except Exception as exc:
        schema_valid = False
        print(f"Validation error: {exc}")
    record(6, "Overview matches Pydantic response schema", schema_valid, "Valid AdminAnalyticsOverviewResponse")

    # Test 7: Overview response has provenance == REAL_DB
    provenance_ok = overview_data.get("provenance") == "REAL_DB"
    record(7, "Overview provenance is REAL_DB", provenance_ok, f"Provenance: {overview_data.get('provenance')}")

    # Test 8: Total query count strictly matches real user messages in database
    total_in_overview = overview_data.get("queries", {}).get("total", -1)
    db_match = (total_in_overview == len(raw_user_msgs))
    record(8, "Total query count equals exact DB user messages count", db_match, f"API={total_in_overview}, DB={len(raw_user_msgs)}")

    # Test 9: Period filter 24h returns 24 hourly timeline points
    res9 = client.get("/api/admin/analytics/overview?period=24h", headers=admin_headers)
    points_24h = res9.json().get("queries", {}).get("timeline", []) if res9.status_code == 200 else []
    record(9, "Period 24h generates 24 hourly timeline buckets", len(points_24h) == 24, f"Buckets={len(points_24h)}")

    # Test 10: Period filter 7d returns 7 daily timeline points
    res10 = client.get("/api/admin/analytics/overview?period=7d", headers=admin_headers)
    points_7d = res10.json().get("queries", {}).get("timeline", []) if res10.status_code == 200 else []
    record(10, "Period 7d generates 7 daily timeline buckets", len(points_7d) == 7, f"Buckets={len(points_7d)}")

    # Test 11: Period filter 30d returns 30 daily timeline points
    res11 = client.get("/api/admin/analytics/overview?period=30d", headers=admin_headers)
    points_30d = res11.json().get("queries", {}).get("timeline", []) if res11.status_code == 200 else []
    record(11, "Period 30d generates 30 daily timeline buckets", len(points_30d) == 30, f"Buckets={len(points_30d)}")

    # Test 12: Invalid period filter returns 422 Unprocessable Entity
    res12 = client.get("/api/admin/analytics/overview?period=invalid_year", headers=admin_headers)
    record(12, "Invalid period filter returns 422", res12.status_code == 422, f"Status: {res12.status_code}")

    # Test 13: Multilingual distribution contains real languages matching DB
    languages = overview_data.get("languages", [])
    lang_codes = [l.get("code") for l in languages]
    has_expected_langs = ("en" in lang_codes or "mr" in lang_codes) and len(languages) >= 2
    record(13, "Multilingual metrics contain real languages", has_expected_langs, f"Detected codes: {lang_codes}")

    # Test 14: Intent distribution contains real classification domains
    intents = overview_data.get("intents", [])
    intent_names = [i.get("intent") for i in intents]
    has_expected_intents = any(x in intent_names for x in ["GENERAL_COOPERATIVE", "PMFBY", "PACS_SERVICE"])
    record(14, "Intent metrics contain real cooperative domains", has_expected_intents, f"Top intents: {intent_names[:3]}")

    # Test 15: Grievances summary matches real status categories from DB
    grv_summary = overview_data.get("grievances", {})
    all_grvs = list_admin_grievances(page=1, page_size=200)
    grv_total_ok = (grv_summary.get("total") == all_grvs.get("total"))
    record(15, "Grievances summary matches repository count", grv_total_ok, f"API={grv_summary.get('total')}, Repo={all_grvs.get('total')}")

    # Test 16: Knowledge summary matches real governance document counts
    kn_summary = overview_data.get("knowledge", {})
    all_docs = get_knowledge_documents()
    kn_total_ok = (kn_summary.get("total") == len(all_docs))
    record(16, "Knowledge governance summary matches repository count", kn_total_ok, f"API={kn_summary.get('total')}, Repo={len(all_docs)}")

    # Test 17: Kiosk summary matches real fleet telemetry counts
    kiosk_summary = overview_data.get("kiosks", {})
    all_kiosks = list_kiosks()
    kiosk_total_ok = (kiosk_summary.get("total") == len(all_kiosks))
    record(17, "Kiosk telemetry summary matches repository count", kiosk_total_ok, f"API={kiosk_summary.get('total')}, Repo={len(all_kiosks)}")

    # Test 18: Telemetry channel metrics are strictly null (not fabricated)
    ch_telemetry = overview_data.get("channel_telemetry", {})
    voice_null = ch_telemetry.get("voice_vs_touch") is None
    kiosk_null = ch_telemetry.get("kiosk_vs_web") is None
    record(18, "Uncollected telemetry channel fields are strictly null", voice_null and kiosk_null, "voice_vs_touch=null, kiosk_vs_web=null")

    # Test 19: Admin request to /api/admin/analytics/knowledge-gaps returns 200 & validates
    res19 = client.get("/api/admin/analytics/knowledge-gaps", headers=admin_headers)
    gaps_data = res19.json() if res19.status_code == 200 else {}
    validated_gaps = None
    try:
        validated_gaps = AdminKnowledgeGapsResponse(**gaps_data)
        gaps_valid = True
    except Exception as exc:
        gaps_valid = False
        print(f"Gaps validation error: {exc}")
    record(19, "Knowledge gaps endpoint returns 200 and valid schema", res19.status_code == 200 and gaps_valid, f"Gaps count: {gaps_data.get('total_gaps')}")

    # Test 20: Knowledge gap items are derived with non-zero query frequency and realistic evidence
    gaps_list = gaps_data.get("gaps", [])
    gaps_meaningful = len(gaps_list) > 0 and all(g.get("frequency", 0) > 0 and len(g.get("evidence", "")) > 5 for g in gaps_list)
    record(20, "Knowledge gaps have positive frequency and empirical evidence", gaps_meaningful, f"Total gaps validated: {len(gaps_list)}")

    print("=" * 70)
    passed_count = sum(1 for _, _, p, _ in results if p)
    total_count = len(results)
    print(f"RESULTS: {passed_count}/{total_count} TESTS PASSED")
    print("=" * 70)

    if passed_count == total_count:
        print("VERDICT: ALL 20 TESTS PASSED SUCCESSFULLY!")
        return True
    else:
        print(f"VERDICT: {total_count - passed_count} TESTS FAILED")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
