"""
Comprehensive test script for Admin-Only Demo Mode.
Validates both ADMIN_DEMO_MODE=true and ADMIN_DEMO_MODE=false behaviors.
"""
import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.config import get_settings
from app.core.security import create_access_token


def run_demo_mode_tests():
    print("=" * 60)
    print("RUNNING ADMIN-ONLY DEMO MODE TEST SUITE")
    print("=" * 60)

    results = []

    def record(test_num, name, passed, details=""):
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] Test {test_num:02d}: {name} - {details}")
        results.append((test_num, name, passed, details))

    # --- PART A: TEST WITH ADMIN_DEMO_MODE=true ---
    os.environ["ADMIN_DEMO_MODE"] = "true"
    get_settings.cache_clear()
    from app.main import app
    client = TestClient(app)

    # 1. Unauthenticated /api/admin/auth/me returns 200 in demo mode
    r = client.get("/api/admin/auth/me")
    passed = r.status_code == 200 and r.json().get("role") == "ADMIN"
    record(1, "Demo Mode: Unauthenticated /api/admin/auth/me", passed, f"Status: {r.status_code}, Role: {r.json().get('role')}")

    # 2. Unauthenticated /api/admin/grievances returns 200 in demo mode
    r = client.get("/api/admin/grievances")
    passed = r.status_code == 200 and "items" in r.json()
    record(2, "Demo Mode: Unauthenticated /api/admin/grievances", passed, f"Status: {r.status_code}, Items: {len(r.json().get('items', []))}")

    # 3. Unauthenticated /api/admin/kiosks returns 200 in demo mode
    r = client.get("/api/admin/kiosks")
    passed = r.status_code == 200 and "items" in r.json()
    record(3, "Demo Mode: Unauthenticated /api/admin/kiosks", passed, f"Status: {r.status_code}, Items: {len(r.json().get('items', []))}")

    # 4. Bearer token still takes precedence when provided in demo mode
    login_res = client.post("/api/admin/auth/login", json={
        "email": "admin@sahkaarsetu.local",
        "password": "SahkaarSetu@Admin2026",
    })
    valid_token = login_res.json().get("access_token")
    r = client.get("/api/admin/auth/me", headers={"Authorization": f"Bearer {valid_token}"})
    passed = r.status_code == 200 and r.json().get("email") == "admin@sahkaarsetu.local"
    record(4, "Demo Mode: Bearer token precedence", passed, f"Status: {r.status_code}, Email: {r.json().get('email')}")

    # 5. Invalid token is rejected even in demo mode (security preservation)
    r = client.get("/api/admin/auth/me", headers={"Authorization": "Bearer invalid.malformed.token"})
    passed = r.status_code == 401
    record(5, "Demo Mode: Invalid token rejection", passed, f"Status: {r.status_code}")

    # --- PART B: TEST WITH ADMIN_DEMO_MODE=false ---
    os.environ["ADMIN_DEMO_MODE"] = "false"
    get_settings.cache_clear()
    client_secure = TestClient(app)

    # 6. Unauthenticated /api/admin/auth/me rejected (401) in secure mode
    r = client_secure.get("/api/admin/auth/me")
    passed = r.status_code == 401
    record(6, "Secure Mode: Unauthenticated /me rejected", passed, f"Status: {r.status_code}")

    # 7. Unauthenticated /api/admin/grievances rejected (401) in secure mode
    r = client_secure.get("/api/admin/grievances")
    passed = r.status_code == 401
    record(7, "Secure Mode: Unauthenticated grievances rejected", passed, f"Status: {r.status_code}")

    # 8. Unauthenticated /api/admin/kiosks rejected (401) in secure mode
    r = client_secure.get("/api/admin/kiosks")
    passed = r.status_code == 401
    record(8, "Secure Mode: Unauthenticated kiosks rejected", passed, f"Status: {r.status_code}")

    # 9. Authenticated request succeeds in secure mode
    r = client_secure.get("/api/admin/auth/me", headers={"Authorization": f"Bearer {valid_token}"})
    passed = r.status_code == 200 and r.json().get("email") == "admin@sahkaarsetu.local"
    record(9, "Secure Mode: Valid token succeeds", passed, f"Status: {r.status_code}")

    # 10. Login endpoint always works in both modes
    r = client_secure.post("/api/admin/auth/login", json={
        "email": "admin@sahkaarsetu.local",
        "password": "SahkaarSetu@Admin2026",
    })
    passed = r.status_code == 200 and "access_token" in r.json()
    record(10, "Login Endpoint Compatibility", passed, f"Status: {r.status_code}")

    print("=" * 60)
    failed_count = sum(1 for _, _, p, _ in results if not p)
    if failed_count == 0:
        print(f"SUCCESS: All {len(results)}/{len(results)} demo mode tests passed successfully!")
    else:
        print(f"FAILURE: {failed_count} test(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    run_demo_mode_tests()
