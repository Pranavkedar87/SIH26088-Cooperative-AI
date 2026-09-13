"""
Automated Test Suite for Citizen Phase 3A.1 — Human Handoff Backend Foundation (SIH26088).
Covers all 17 required verification checks:
1. Endpoint exists
2. Valid handoff succeeds
3. Existing grievance endpoint still works
4. Existing create_grievance callers remain compatible
5. Marathi -> English translation path is attempted when required
6. English -> Marathi translation path is attempted when required
7. Same-language request skips translation
8. Translation failure does not create false translation success
9. Unique reference code generated
10. Conversation ID persisted when supplied
11. Category persisted
12. PACS name persisted when supplied
13. Sensitive credentials are not stored
14. Disclaimer returned
15. Empty/optional citizen fields handled safely
16. Invalid payload rejected
17. Database failure cannot produce success response
"""
import os
import sys
import re
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ENVIRONMENT", "development")

from app.main import app
from database.repository import (
    create_grievance,
    get_grievance,
    _DEV_GRIEVANCES_FALLBACK,
    list_admin_grievances,
)

client = TestClient(app)

def run_tests():
    print("============================================================")
    print("RUNNING CITIZEN PHASE 3A.1 HUMAN HANDOFF BACKEND TEST SUITE")
    print("============================================================")
    passed_count = 0
    total_checks = 17

    # 1. Endpoint exists
    res1 = client.post("/api/grievance/handoff", json={})
    assert res1.status_code == 422, f"Expected 422 for empty payload, got {res1.status_code}"
    print("[PASSED] 1. Endpoint exists: POST /api/grievance/handoff returned 422 on empty request")
    passed_count += 1

    # 2. Valid handoff succeeds
    valid_payload = {
        "conversation_id": "test-conv-1234",
        "language": "mr",
        "target_officer_language": "en",
        "citizen_name": "Tukaram Patil",
        "citizen_phone": "+91 9822112345",
        "pacs_name": "Dindori Primary Agriculture Cooperative Society",
        "village": "Dindori",
        "category": "PMFBY",
        "description": "माझ्या पिकाचे अवकाळी पावसामुळे ७०% नुकसान झाले असून भरपाई हवी आहे.",
        "ai_guidance": "PMFBY नियमानुसार ७२ तासांच्या आत नुकसानीची पूर्वसूचना PACS किंवा विमा कंपनीकडे देणे आवश्यक आहे.",
        "source_citations": [
            {"title": "PMFBY Operational Guidelines Cl. 15", "source_name": "Ministry of Agriculture"}
        ],
        "priority": "high",
    }
    with patch("app.providers.bhashini_provider.BhashiniProvider.translate_text", new_callable=AsyncMock) as mock_trans:
        mock_trans.return_value = "70% of crop damaged due to unseasonal rain, compensation required."
        res2 = client.post("/api/grievance/handoff", json=valid_payload)
    assert res2.status_code == 201, f"Expected 201, got {res2.status_code}: {res2.text}"
    data2 = res2.json()
    assert data2["success"] is True
    assert "PACS-2026-" in data2["reference_code"]
    print(f"[PASSED] 2. Valid handoff succeeds: Code={data2['reference_code']}, ID={data2['grievance_id']}")
    passed_count += 1

    # 3. Existing grievance endpoint still works
    res3 = client.post("/api/grievance", json={
        "category": "PACS",
        "description": "General enquiry about fertilizer stock at local society.",
        "language": "en",
    })
    assert res3.status_code == 201, f"Expected 201, got {res3.status_code}"
    data3 = res3.json()
    assert "grievance_id" in data3
    assert data3["status"] == "draft"
    print(f"[PASSED] 3. Existing grievance endpoint still works: ID={data3['grievance_id']}")
    passed_count += 1

    # 4. Existing create_grievance callers remain compatible
    legacy_id = create_grievance(
        conversation_id="conv-legacy-001",
        category="LOAN_ISSUE",
        description="Legacy caller with 4 positional arguments only",
        status="draft",
    )
    assert legacy_id is not None
    rec_legacy = get_grievance(legacy_id)
    assert rec_legacy["description"] == "Legacy caller with 4 positional arguments only"
    assert rec_legacy["category"] == "LOAN_ISSUE"
    print(f"[PASSED] 4. Existing create_grievance callers remain compatible: ID={legacy_id}")
    passed_count += 1

    # 5. Marathi -> English translation path is attempted when required
    with patch("app.providers.bhashini_provider.BhashiniProvider.translate_text", new_callable=AsyncMock) as mock_mr_en:
        mock_mr_en.return_value = "Translated English summary for officer"
        res5 = client.post("/api/grievance/handoff", json={
            "language": "mr",
            "target_officer_language": "en",
            "category": "PACS_SERVICE",
            "description": "खतांचा साठा संपला आहे आणि नवीन साठा कधी येणार?",
        })
        assert res5.status_code == 201
        data5 = res5.json()
        assert data5["translation_status"] == "translated"
        assert data5["translated_summary"] == "Translated English summary for officer"
        mock_mr_en.assert_called_once()
    print("[PASSED] 5. Marathi -> English translation path is attempted when required")
    passed_count += 1

    # 6. English -> Marathi translation path is attempted when required
    with patch("app.providers.bhashini_provider.BhashiniProvider.translate_text", new_callable=AsyncMock) as mock_en_mr:
        mock_en_mr.return_value = "अधिकारी सारांश मराठीत"
        res6 = client.post("/api/grievance/handoff", json={
            "language": "en",
            "target_officer_language": "mr",
            "category": "COOPERATIVE_LAW",
            "description": "How to dispute annual general meeting notice irregularities?",
        })
        assert res6.status_code == 201
        data6 = res6.json()
        assert data6["translation_status"] == "translated"
        assert data6["translated_summary"] == "अधिकारी सारांश मराठीत"
        mock_en_mr.assert_called_once()
    print("[PASSED] 6. English -> Marathi translation path is attempted when required")
    passed_count += 1

    # 7. Same-language request skips translation
    with patch("app.providers.bhashini_provider.BhashiniProvider.translate_text", new_callable=AsyncMock) as mock_same:
        res7 = client.post("/api/grievance/handoff", json={
            "language": "mr",
            "target_officer_language": "mr",
            "category": "PMFBY",
            "description": "समान भाषेतील तक्रार नोंदणी चाचणी.",
        })
        assert res7.status_code == 201
        data7 = res7.json()
        assert data7["translation_status"] == "same_language"
        assert data7["translated_summary"] == "समान भाषेतील तक्रार नोंदणी चाचणी."
        mock_same.assert_not_called()
    print("[PASSED] 7. Same-language request skips translation without invoking NMT")
    passed_count += 1

    # 8. Translation failure does not create false translation success
    with patch("app.providers.bhashini_provider.BhashiniProvider.translate_text", new_callable=AsyncMock) as mock_fail:
        mock_fail.side_effect = TimeoutError("Bhashini translation gateway timeout")
        res8 = client.post("/api/grievance/handoff", json={
            "language": "mr",
            "target_officer_language": "en",
            "category": "PMFBY",
            "description": "अनुवाद अयशस्वी चाचणी.",
        })
        assert res8.status_code == 201
        data8 = res8.json()
        assert data8["translation_status"] == "untranslated_fallback"
        assert data8["translated_summary"] == "अनुवाद अयशस्वी चाचणी."
    print("[PASSED] 8. Translation failure does not create false translation success (fallback stored safely)")
    passed_count += 1

    # 9. Unique reference code generated
    ref_codes = set()
    for _ in range(5):
        r = client.post("/api/grievance/handoff", json={
            "category": "TEST",
            "description": "Testing deterministic uniqueness of reference codes.",
        })
        assert r.status_code == 201
        code = r.json()["reference_code"]
        assert re.match(r"^PACS-2026-[2-9A-HJ-NP-Z]{6}$", code), f"Invalid code format: {code}"
        ref_codes.add(code)
    assert len(ref_codes) == 5, "Reference codes must be unique"
    print(f"[PASSED] 9. Unique reference code generated: Sample={list(ref_codes)[0]}")
    passed_count += 1

    # 10. Conversation ID persisted when supplied
    test_conv_id = "test-conv-persist-999"
    res10 = client.post("/api/grievance/handoff", json={
        "conversation_id": test_conv_id,
        "category": "PACS",
        "description": "Check conversation id persistence into repository.",
    })
    assert res10.status_code == 201
    g_id_10 = res10.json()["grievance_id"]
    rec10 = get_grievance(g_id_10)
    assert rec10["conversation_id"] == test_conv_id
    print(f"[PASSED] 10. Conversation ID persisted when supplied: {test_conv_id}")
    passed_count += 1

    # 11. Category persisted
    test_cat = "CROP_DAMAGE_EMERGENCY"
    res11 = client.post("/api/grievance/handoff", json={
        "category": test_cat,
        "description": "Check category persistence into database repository.",
    })
    assert res11.status_code == 201
    g_id_11 = res11.json()["grievance_id"]
    rec11 = get_grievance(g_id_11)
    assert rec11["category"] == test_cat
    print(f"[PASSED] 11. Category persisted: {test_cat}")
    passed_count += 1

    # 12. PACS name persisted when supplied
    test_pacs = "Baramati Taluka Sahakari Sangh"
    res12 = client.post("/api/grievance/handoff", json={
        "category": "PACS_SERVICE",
        "pacs_name": test_pacs,
        "description": "Check pacs_name persistence for admin triage.",
    })
    assert res12.status_code == 201
    g_id_12 = res12.json()["grievance_id"]
    rec12 = get_grievance(g_id_12)
    assert rec12["pacs_name"] == test_pacs
    # Verify Admin listing search finds it by pacs_name or reference code
    admin_list = list_admin_grievances(pacs="Baramati", user={"role": "ADMIN"})
    assert any(item["id"] == g_id_12 for item in admin_list["items"])
    print(f"[PASSED] 12. PACS name persisted and visible in admin triage: {test_pacs}")
    passed_count += 1

    # 13. Sensitive credentials are not stored and phone is masked
    raw_phone = "+91 98221 98765"
    raw_name = "Shrirang Bhaurao Kadam"
    res13 = client.post("/api/grievance/handoff", json={
        "category": "PRIVACY_TEST",
        "description": "Privacy check on phone and citizen name masking.",
        "citizen_name": raw_name,
        "citizen_phone": raw_phone,
    })
    assert res13.status_code == 201
    data13 = res13.json()
    assert data13["citizen_phone_masked"] != raw_phone
    assert "•••••" in data13["citizen_phone_masked"]
    assert "Shrirang" in data13["citizen_masked_name"] and "****" in data13["citizen_masked_name"]
    # Check DB record
    rec13 = get_grievance(data13["grievance_id"])
    assert rec13["citizen_phone_masked"] != raw_phone
    # Verify response body has zero leaks
    resp_text = res13.text
    assert "BHASHINI_API_KEY" not in resp_text
    assert "SUPABASE" not in resp_text
    print(f"[PASSED] 13. Sensitive credentials protected and phone masked: {data13['citizen_phone_masked']}")
    passed_count += 1

    # 14. Disclaimer returned
    res14 = client.post("/api/grievance/handoff", json={
        "category": "PACS",
        "description": "Checking facilitation disclaimer compliance.",
    })
    assert res14.status_code == 201
    disclaimer = res14.json()["disclaimer"]
    assert "facilitation slip" in disclaimer.lower()
    assert "not a court summons" in disclaimer.lower()
    assert "not a court summons, registrar order, or confirmation of official filing" in disclaimer.lower()
    print("[PASSED] 14. Facilitation disclaimer returned accurately on all slips")
    passed_count += 1

    # 15. Empty/optional citizen fields handled safely
    res15 = client.post("/api/grievance/handoff", json={
        "category": "MINIMAL_PAYLOAD",
        "description": "Checking minimal payload without any optional fields.",
        "citizen_name": None,
        "citizen_phone": None,
        "pacs_name": None,
        "village": None,
        "ai_guidance": None,
        "source_citations": None,
    })
    assert res15.status_code == 201
    data15 = res15.json()
    assert data15["citizen_masked_name"] == "Citizen (Protected)"
    assert data15["citizen_phone_masked"] == "+91 98******45"
    assert data15["pacs_name"] is None
    assert data15["slip_data"]["pacs_name"] == "Local PACS (Unspecified)"
    print("[PASSED] 15. Empty/optional citizen fields handled safely with protected defaults")
    passed_count += 1

    # 16. Invalid payload rejected
    res16_short = client.post("/api/grievance/handoff", json={
        "category": "PMFBY",
        "description": "abc",  # less than 5 chars
    })
    assert res16_short.status_code == 422
    res16_no_cat = client.post("/api/grievance/handoff", json={
        "description": "Valid description length but missing required category field.",
    })
    assert res16_no_cat.status_code == 422
    print("[PASSED] 16. Invalid payload rejected with HTTP 422")
    passed_count += 1

    # 17. Database failure cannot produce success response
    with patch("app.api.routes.grievance.create_grievance") as mock_db_fail:
        mock_db_fail.return_value = None  # DB creation failed
        res17 = client.post("/api/grievance/handoff", json={
            "category": "DB_FAILURE_TEST",
            "description": "Simulating database failure to verify zero false success.",
        })
        assert res17.status_code == 500, f"Expected 500 on DB failure, got {res17.status_code}"
    print("[PASSED] 17. Database failure cannot produce false success response (HTTP 500 returned)")
    passed_count += 1

    print("============================================================")
    print(f"RESULTS: {passed_count}/{total_checks} CHECKS PASSED (100%)")
    print("============================================================")

if __name__ == "__main__":
    run_tests()
