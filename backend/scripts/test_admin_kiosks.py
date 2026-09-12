"""
Comprehensive Test Suite for Phase 2A.3: Kiosk Fleet Monitoring & Telemetry.
Tests all 19 mandatory test cases against the FastAPI application.
"""
import os
import sys
from datetime import datetime, timezone

# Ensure backend root is on PYTHONPATH
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("=" * 70)
    print("RUNNING PHASE 2A.3 KIOSK FLEET MONITORING TEST SUITE")
    print("=" * 70)

    results = []

    def record(test_num: int, name: str, passed: bool, details: str = ""):
        status_str = "PASSED" if passed else "FAILED"
        print(f"[{status_str}] Test {test_num:02d}: {name} - {details}")
        results.append((test_num, name, passed, details))

    # Obtain tokens for Admin and Staff
    login_admin = client.post("/api/admin/auth/login", json={
        "email": "admin@sahkaarsetu.local",
        "password": "SahkaarSetu@Admin2026",
    }).json()
    admin_token = login_admin.get("access_token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    login_staff = client.post("/api/admin/auth/login", json={
        "email": "staff@sahkaarsetu.local",
        "password": "SahkaarSetu@Staff2026",
    }).json()
    staff_token = login_staff.get("access_token")
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # 1. Admin can list kiosks (200)
    res = client.get("/api/admin/kiosks", headers=admin_headers)
    passed = res.status_code == 200 and "items" in res.json() and "total" in res.json()
    record(1, "Admin Can List Kiosks", passed, f"Status: {res.status_code}, Total: {res.json().get('total')}")

    # 2. STAFF only sees assigned PACS kiosks (Dindori Primary Agriculture Cooperative Society)
    res_staff = client.get("/api/admin/kiosks", headers=staff_headers)
    staff_items = res_staff.json().get("items", [])
    staff_leaks = [
        k for k in staff_items
        if "Dindori" not in (k.get("pacs_name") or "")
    ]
    passed = res_staff.status_code == 200 and len(staff_items) == 1 and len(staff_leaks) == 0
    record(2, "STAFF Isolation (Only Assigned PACS)", passed, f"Count: {len(staff_items)}, Leaks: {len(staff_leaks)}")

    # 3. ADMIN sees all kiosks across all PACS
    admin_items = res.json().get("items", [])
    passed = len(admin_items) >= 4
    record(3, "ADMIN Global Fleet Visibility", passed, f"Total visible kiosks: {len(admin_items)}")

    # 4. Single kiosk detail returns 200 with complete diagnostics
    res_detail = client.get("/api/admin/kiosks/KSK-001", headers=admin_headers)
    data = res_detail.json()
    passed = (
        res_detail.status_code == 200
        and data.get("id") == "KSK-001"
        and "health" in data
        and "device" in data["health"]
        and "printer" in data["health"]
        and "network" in data["health"]
        and "sync" in data["health"]
    )
    record(4, "Single Kiosk Detail With Subsystem Health", passed, f"Status: {res_detail.status_code}, Health: {data.get('health')}")

    # 5. District filter works
    res_dist = client.get("/api/admin/kiosks?district=Pune", headers=admin_headers)
    items_dist = res_dist.json().get("items", [])
    passed = res_dist.status_code == 200 and all(k.get("district") == "Pune" for k in items_dist) and len(items_dist) > 0
    record(5, "District Filter (Pune)", passed, f"Matches: {len(items_dist)}")

    # 6. PACS filter works
    res_pacs = client.get("/api/admin/kiosks?pacs=Dindori", headers=admin_headers)
    items_pacs = res_pacs.json().get("items", [])
    passed = res_pacs.status_code == 200 and all("Dindori" in k.get("pacs_name", "") for k in items_pacs) and len(items_pacs) == 1
    record(6, "PACS Society Filter", passed, f"Matches: {len(items_pacs)}")

    # 7. Status filter works
    res_st = client.get("/api/admin/kiosks?status=online", headers=admin_headers)
    items_st = res_st.json().get("items", [])
    passed = res_st.status_code == 200 and all(k.get("status") == "online" for k in items_st)
    record(7, "Status Filter (online)", passed, f"Online kiosks count: {len(items_st)}")

    # 8. Free-text search works
    res_search = client.get("/api/admin/kiosks?search=Baramati", headers=admin_headers)
    items_search = res_search.json().get("items", [])
    passed = res_search.status_code == 200 and len(items_search) == 1 and items_search[0]["id"] == "KSK-002"
    record(8, "Free-Text Search (Baramati)", passed, f"Matches: {[k['id'] for k in items_search]}")

    # 9. Maintenance update works via PATCH
    res_patch = client.patch(
        "/api/admin/kiosks/KSK-001",
        headers=admin_headers,
        json={"status": "maintenance", "notes": "Touchscreen alignment scheduled"}
    )
    patched_data = res_patch.json()
    passed = (
        res_patch.status_code == 200
        and patched_data.get("status") == "maintenance"
        and "Touchscreen alignment" in patched_data.get("notes", "")
    )
    record(9, "Maintenance Status Transition (PATCH)", passed, f"Status: {patched_data.get('status')}, Notes: {patched_data.get('notes')}")

    # 10. Unauthorized request returns 401
    res_unauth = client.get("/api/admin/kiosks")
    passed = res_unauth.status_code == 401
    record(10, "Unauthorized Access Rejected (401)", passed, f"Status: {res_unauth.status_code}")

    # 11. STAFF requesting unauthorized kiosk returns 403
    # KSK-002 belongs to Baramati Taluka Cooperative, Staff is Dindori only
    res_forbidden = client.get("/api/admin/kiosks/KSK-002", headers=staff_headers)
    passed = res_forbidden.status_code == 403
    record(11, "Staff Forbidden For Other PACS (403)", passed, f"Status: {res_forbidden.status_code}")

    # 12. Requesting unknown kiosk returns 404
    res_notfound = client.get("/api/admin/kiosks/KSK-99999", headers=admin_headers)
    passed = res_notfound.status_code == 404
    record(12, "Unknown Kiosk Returns 404", passed, f"Status: {res_notfound.status_code}")

    # 13. M2M heartbeat with valid kiosk key returns 200
    res_hb = client.post(
        "/api/kiosks/KSK-001/heartbeat",
        headers={"X-Kiosk-Key": "kiosk-secret-dindori-001"},
        json={
            "software_version": "v2.4.2",
            "device_status": "ok",
            "network_status": "online",
            "printer_status": "ready",
            "sync_status": "synced",
            "ip_address": "192.168.1.101"
        }
    )
    hb_data = res_hb.json()
    passed = res_hb.status_code == 200 and hb_data.get("status") == "ok" and hb_data.get("kiosk_id") == "KSK-001"
    record(13, "M2M Heartbeat Ingestion (Valid Key)", passed, f"Status: {res_hb.status_code}, State: {hb_data.get('state')}")

    # 14. M2M heartbeat with invalid/missing key returns 401
    res_hb_bad = client.post(
        "/api/kiosks/KSK-001/heartbeat",
        headers={"X-Kiosk-Key": "wrong-secret-key"},
        json={"device_status": "ok"}
    )
    passed = res_hb_bad.status_code == 401
    record(14, "M2M Heartbeat Rejected (Invalid Key)", passed, f"Status: {res_hb_bad.status_code}")

    # 15. Heartbeat updates last_heartbeat timestamp
    res_check = client.get("/api/admin/kiosks/KSK-001", headers=admin_headers).json()
    last_hb_str = res_check.get("last_heartbeat")
    passed = False
    if last_hb_str:
        dt = datetime.fromisoformat(last_hb_str)
        now = datetime.now(timezone.utc)
        diff_sec = abs((now - dt).total_seconds())
        passed = diff_sec < 60  # updated within the last minute
    record(15, "Heartbeat Updates last_heartbeat", passed, f"Last Heartbeat: {last_hb_str}")

    # 16. Heartbeat updates health diagnostic subsystems
    client.post(
        "/api/kiosks/KSK-001/heartbeat",
        headers={"X-Kiosk-Key": "kiosk-secret-dindori-001"},
        json={
            "device_status": "degraded",
            "printer_status": "low_paper",
            "network_status": "weak"
        }
    )
    res_diag = client.get("/api/admin/kiosks/KSK-001", headers=admin_headers).json()
    health = res_diag.get("health", {})
    passed = (
        health.get("device") == "degraded"
        and health.get("printer") == "low_paper"
        and health.get("network") == "weak"
    )
    record(16, "Heartbeat Updates Diagnostic Subsystems", passed, f"Health: {health}")

    # 17. Heartbeat cannot modify arbitrary/unauthorized columns
    res_hb_tamper = client.post(
        "/api/kiosks/KSK-001/heartbeat",
        headers={"X-Kiosk-Key": "kiosk-secret-dindori-001"},
        json={
            "location": "Arbitrary Location Override Attempt",
            "pacs_name": "Tampered PACS Name",
            "uptime_percent": 100.0,
        }
    )
    res_after = client.get("/api/admin/kiosks/KSK-001", headers=admin_headers).json()
    passed = (
        res_hb_tamper.status_code == 200
        and res_after.get("location") != "Arbitrary Location Override Attempt"
        and "Dindori" in res_after.get("pacs_name", "")
    )
    record(17, "Heartbeat Cannot Modify Arbitrary Columns", passed, f"Location preserved: {res_after.get('location')}")

    # 18. Remote reboot endpoint does NOT exist (returns 404 or 405)
    res_reboot_1 = client.post("/api/kiosks/KSK-001/reboot", headers=admin_headers)
    res_reboot_2 = client.post("/api/admin/kiosks/KSK-001/reboot", headers=admin_headers)
    passed = (res_reboot_1.status_code in (404, 405)) and (res_reboot_2.status_code in (404, 405))
    record(18, "Remote Reboot Strictly Blocked / Non-Existent", passed, f"Paths returned: {res_reboot_1.status_code}, {res_reboot_2.status_code}")

    # 19. Existing Citizen endpoints remain compatible
    res_health = client.get("/health")
    passed = res_health.status_code == 200 and res_health.json().get("status") == "ok"
    record(19, "Citizen API Regression Immunity", passed, f"Health status: {res_health.json()}")

    print("=" * 70)
    all_passed = all(r[2] for r in results)
    pass_count = sum(1 for r in results if r[2])
    print(f"RESULTS: {pass_count}/{len(results)} TESTS PASSED")
    if all_passed:
        print("ALL KIOSK FLEET TESTS PASSED.")
    else:
        print("SOME TESTS FAILED.")
    print("=" * 70)

    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
