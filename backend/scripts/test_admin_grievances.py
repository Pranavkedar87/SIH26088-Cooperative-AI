"""
Verification script for Phase 2A.2: Admin Grievance Triage.
Tests all 19 test cases against FastAPI application using TestClient.
"""
import os
import sys

# Ensure backend root is on PYTHONPATH
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("RUNNING PHASE 2A.2 ADMIN GRIEVANCE TRIAGE TEST SUITE")
    print("=" * 60)

    results = []

    def record(test_num, name, passed, details=""):
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] Test {test_num:02d}: {name} - {details}")
        results.append((test_num, name, passed, details))

    # Obtain tokens for Admin and Staff
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

    # 1. Admin can list grievances (200)
    res = client.get("/api/admin/grievances", headers=admin_headers)
    passed = res.status_code == 200 and "items" in res.json() and "total" in res.json()
    record(1, "Admin Can List Grievances", passed, f"Status: {res.status_code}, Total: {res.json().get('total')}")

    # 2. STAFF can only access authorized grievances
    res_staff_list = client.get("/api/admin/grievances", headers=staff_headers)
    staff_items = res_staff_list.json().get("items", [])
    # Staff Sunil Patil is assigned to Dindori PACS
    # All items returned must have pacs_name == Dindori PACS or assigned_staff == Sunil Patil
    unauthorized_leaks = [
        item for item in staff_items
        if "Dindori" not in (item.get("pacs_name") or "") and "Sunil" not in (item.get("assigned_staff") or "")
    ]
    passed = res_staff_list.status_code == 200 and len(unauthorized_leaks) == 0 and len(staff_items) > 0
    record(2, "STAFF Isolation (Only Authorized Cases)", passed, f"Staff items count: {len(staff_items)}, Leaks: {len(unauthorized_leaks)}")

    # 3. ADMIN can access all grievances
    admin_items = res.json().get("items", [])
    passed = len(admin_items) > len(staff_items)
    record(3, "ADMIN Accesses All Cases Unrestricted", passed, f"Admin count: {len(admin_items)} vs Staff count: {len(staff_items)}")

    # 4. Pagination works
    res_page = client.get("/api/admin/grievances?page=1&page_size=2", headers=admin_headers)
    p_data = res_page.json()
    passed = res_page.status_code == 200 and len(p_data.get("items", [])) == 2 and p_data.get("page") == 1 and p_data.get("page_size") == 2
    record(4, "Pagination Enforcement", passed, f"Items returned: {len(p_data.get('items', []))}, Page: {p_data.get('page')}")

    # 5. Status filter works
    res_status = client.get("/api/admin/grievances?status=resolved", headers=admin_headers)
    s_items = res_status.json().get("items", [])
    passed = res_status.status_code == 200 and all(it.get("status") == "resolved" for it in s_items) and len(s_items) > 0
    record(5, "Status Filter", passed, f"Resolved items found: {len(s_items)}")

    # 6. Priority filter works
    res_prio = client.get("/api/admin/grievances?priority=urgent", headers=admin_headers)
    p_items = res_prio.json().get("items", [])
    passed = res_prio.status_code == 200 and all(it.get("priority") == "urgent" for it in p_items) and len(p_items) > 0
    record(6, "Priority Filter", passed, f"Urgent items found: {len(p_items)}")

    # 7. Category filter works
    res_cat = client.get("/api/admin/grievances?category=PMFBY", headers=admin_headers)
    c_items = res_cat.json().get("items", [])
    passed = res_cat.status_code == 200 and all(it.get("category") == "PMFBY" for it in c_items) and len(c_items) > 0
    record(7, "Category Filter", passed, f"PMFBY items found: {len(c_items)}")

    # 8. PATCH status works
    # GRV-2026-001 is currently 'under_review', valid transition is 'resolved'
    res_patch_status = client.patch(
        "/api/admin/grievances/GRV-2026-001",
        headers=admin_headers,
        json={"status": "resolved"}
    )
    passed = res_patch_status.status_code == 200 and res_patch_status.json().get("status") == "resolved"
    record(8, "PATCH Status Transition", passed, f"Status: {res_patch_status.status_code}, New status: {res_patch_status.json().get('status')}")

    # 9. PATCH priority works
    res_patch_prio = client.patch(
        "/api/admin/grievances/GRV-2026-001",
        headers=admin_headers,
        json={"priority": "high"}
    )
    passed = res_patch_prio.status_code == 200 and res_patch_prio.json().get("priority") == "high"
    record(9, "PATCH Priority Update", passed, f"Status: {res_patch_prio.status_code}, Priority: {res_patch_prio.json().get('priority')}")

    # 10. PATCH assignment works
    res_patch_assign = client.patch(
        "/api/admin/grievances/GRV-2026-001",
        headers=admin_headers,
        json={"assigned_staff": "Aniket Shinde (DDR Officer)"}
    )
    passed = res_patch_assign.status_code == 200 and res_patch_assign.json().get("assigned_staff") == "Aniket Shinde (DDR Officer)"
    record(10, "PATCH Staff Assignment", passed, f"Assigned: {res_patch_assign.json().get('assigned_staff')}")

    # 11. Internal note is appended, not overwritten
    note_text_1 = "Initial inspection completed on site."
    res_note_1 = client.post(
        "/api/admin/grievances/GRV-2026-001/notes",
        headers=admin_headers,
        json={"note": note_text_1}
    )
    notes_1 = res_note_1.json().get("staff_notes", [])

    note_text_2 = "Second follow-up verification with talathi."
    res_note_2 = client.post(
        "/api/admin/grievances/GRV-2026-001/notes",
        headers=admin_headers,
        json={"note": note_text_2}
    )
    notes_2 = res_note_2.json().get("staff_notes", [])

    passed = (
        res_note_2.status_code == 200
        and len(notes_2) == len(notes_1) + 1
        and any(n.get("note") == note_text_1 for n in notes_2)
        and any(n.get("note") == note_text_2 for n in notes_2)
    )
    record(11, "Internal Note Append (History Preserved)", passed, f"Total notes now: {len(notes_2)}")

    # 12. Unauthorized user -> 401
    res_unauth = client.get("/api/admin/grievances")
    passed = res_unauth.status_code == 401
    record(12, "Unauthorized Access Rejection", passed, f"Status: {res_unauth.status_code}")

    # 13. STAFF accessing unauthorized case -> 403
    # GRV-2026-002 is in Baramati PACS and assigned to Pooja Deshmukh; Sunil Patil (staff) should be rejected
    res_staff_forbidden = client.get("/api/admin/grievances/GRV-2026-002", headers=staff_headers)
    passed = res_staff_forbidden.status_code == 403
    record(13, "STAFF Forbidden on Unauthorized Case", passed, f"Status: {res_staff_forbidden.status_code}")

    # 14. Invalid grievance ID -> 404
    res_not_found = client.get("/api/admin/grievances/NON-EXISTENT-ID-9999", headers=admin_headers)
    passed = res_not_found.status_code == 404
    record(14, "Invalid Grievance ID Rejection", passed, f"Status: {res_not_found.status_code}")

    # 15. Invalid status transition -> 400
    # Re-fetch GRV-2026-002 (submitted). Trying to jump directly to 'closed' is invalid
    res_bad_trans = client.patch(
        "/api/admin/grievances/GRV-2026-002",
        headers=admin_headers,
        json={"status": "closed"}
    )
    passed = res_bad_trans.status_code == 400 and "invalid status transition" in res_bad_trans.json().get("detail", "").lower()
    record(15, "Invalid Status Transition Rejection", passed, f"Status: {res_bad_trans.status_code}, Detail: {res_bad_trans.json().get('detail')}")

    # 16. Citizen PII is masked
    detail_res = client.get("/api/admin/grievances/GRV-2026-001", headers=admin_headers).json()
    masked_name = detail_res.get("citizen_masked_name", "")
    masked_phone = detail_res.get("citizen_phone_masked", "")
    # Check that masking characters or protected notice exist
    passed = (
        ("*" in masked_name or "••••" in masked_name or "Protected" in masked_name)
        and ("*" in masked_phone or "••••" in masked_phone)
    )
    record(16, "Citizen PII Masking Verification", passed, f"Name: {masked_name}, Phone: {masked_phone}")

    # 17. Existing POST /api/grievance remains compatible
    citizen_create = client.post("/api/grievance", json={
        "description": "Fertilizer distribution register mismatch at local branch.",
        "category": "PACS",
        "language": "mr"
    })
    c_data = citizen_create.json() if citizen_create.status_code == 201 else {}
    passed = citizen_create.status_code == 201 and "grievance_id" in c_data
    new_citizen_grv_id = c_data.get("grievance_id")
    record(17, "Existing POST /api/grievance Compatibility", passed, f"Status: {citizen_create.status_code}, ID: {new_citizen_grv_id}")

    # 18. Existing GET /api/grievance/{id} remains compatible
    res_c_get = client.get(f"/api/grievance/{new_citizen_grv_id}")
    passed = res_c_get.status_code == 200 and res_c_get.json().get("grievance_id") == new_citizen_grv_id
    record(18, "Existing GET /api/grievance/{id} Compatibility", passed, f"Status: {res_c_get.status_code}")

    # 19. Existing GET /api/grievance/{id}/summary remains compatible
    res_c_sum = client.get(f"/api/grievance/{new_citizen_grv_id}/summary")
    passed = res_c_sum.status_code == 200 and "summary" in res_c_sum.json()
    record(19, "Existing GET /api/grievance/{id}/summary Compatibility", passed, f"Status: {res_c_sum.status_code}")

    print("=" * 60)
    failed = [r for r in results if not r[2]]
    if failed:
        print(f"FAILED: {len(failed)} tests failed.")
        sys.exit(1)
    else:
        print(f"SUCCESS: All {len(results)}/19 tests passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    run_tests()
