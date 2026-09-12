"""
Verification script for Phase 2A.1: Admin Authentication.
Tests all 12 test cases against FastAPI application using TestClient.
"""
import sys
import os

# Ensure backend root is on PYTHONPATH
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, get_password_hash
from database.repository import _DEV_USERS_FALLBACK, _init_dev_users_fallback

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("RUNNING PHASE 2A.1 ADMIN AUTHENTICATION TEST SUITE")
    print("=" * 60)

    results = []

    def record(test_num, name, passed, details=""):
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] Test {test_num}: {name} - {details}")
        results.append((test_num, name, passed, details))

    # Test 1: Valid Admin login
    res = client.post("/api/admin/auth/login", json={
        "email": "admin@sahkaarsetu.local",
        "password": "SahkaarSetu@Admin2026"
    })
    data = res.json() if res.status_code == 200 else {}
    passed = (
        res.status_code == 200
        and "access_token" in data
        and data.get("user", {}).get("role") == "ADMIN"
        and data.get("user", {}).get("email") == "admin@sahkaarsetu.local"
    )
    admin_token = data.get("access_token")
    record(1, "Valid Admin Login", passed, f"Status: {res.status_code}")

    # Test 2: Valid Staff login
    res = client.post("/api/admin/auth/login", json={
        "email": "staff@sahkaarsetu.local",
        "password": "SahkaarSetu@Staff2026"
    })
    data = res.json() if res.status_code == 200 else {}
    passed = (
        res.status_code == 200
        and "access_token" in data
        and data.get("user", {}).get("role") == "STAFF"
        and data.get("user", {}).get("email") == "staff@sahkaarsetu.local"
    )
    staff_token = data.get("access_token")
    record(2, "Valid Staff Login", passed, f"Status: {res.status_code}")

    # Test 3: Invalid password
    res = client.post("/api/admin/auth/login", json={
        "email": "admin@sahkaarsetu.local",
        "password": "WrongPassword123!"
    })
    passed = res.status_code == 401 and "invalid email or password" in res.json().get("detail", "").lower()
    record(3, "Invalid Password Rejection", passed, f"Status: {res.status_code}, Detail: {res.json().get('detail')}")

    # Test 4: Unknown email
    res = client.post("/api/admin/auth/login", json={
        "email": "nonexistent.user@sahkaarsetu.local",
        "password": "SahkaarSetu@Admin2026"
    })
    passed = res.status_code == 401 and "invalid email or password" in res.json().get("detail", "").lower()
    record(4, "Unknown Email Rejection", passed, f"Status: {res.status_code}, Detail: {res.json().get('detail')}")

    # Test 5: Inactive account
    _init_dev_users_fallback()
    _DEV_USERS_FALLBACK["inactive@sahkaarsetu.local"] = {
        "id": "USR-TEST-INACTIVE",
        "email": "inactive@sahkaarsetu.local",
        "password_hash": get_password_hash("InactivePass123!"),
        "full_name": "Inactive Admin",
        "role": "ADMIN",
        "assigned_pacs": None,
        "is_active": False,
        "last_login": None,
    }
    res = client.post("/api/admin/auth/login", json={
        "email": "inactive@sahkaarsetu.local",
        "password": "InactivePass123!"
    })
    passed = res.status_code == 403 and "deactivated" in res.json().get("detail", "").lower()
    record(5, "Inactive Account Rejection", passed, f"Status: {res.status_code}, Detail: {res.json().get('detail')}")

    # Test 6: Valid token on /api/admin/auth/me
    res = client.get("/api/admin/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    data = res.json() if res.status_code == 200 else {}
    passed = res.status_code == 200 and data.get("email") == "admin@sahkaarsetu.local" and data.get("role") == "ADMIN"
    record(6, "Valid Token on /api/admin/auth/me", passed, f"Status: {res.status_code}, User: {data.get('email')}")

    # Test 7: Missing token on /api/admin/auth/me
    res = client.get("/api/admin/auth/me")
    passed = res.status_code in (401, 403)
    record(7, "Missing Token Rejection", passed, f"Status: {res.status_code}")

    # Test 8: Invalid token on /api/admin/auth/me
    res = client.get("/api/admin/auth/me", headers={"Authorization": "Bearer not.a.valid.jwt.token"})
    passed = res.status_code == 401
    record(8, "Invalid Token Rejection", passed, f"Status: {res.status_code}, Detail: {res.json().get('detail')}")

    # Test 9: Expired token on /api/admin/auth/me
    from datetime import timedelta
    expired_token, _ = create_access_token(
        subject="USR-ADM-DEV-001",
        role="ADMIN",
        expires_delta=timedelta(seconds=-10)
    )
    res = client.get("/api/admin/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    passed = res.status_code == 401 and "expired" in res.json().get("detail", "").lower()
    record(9, "Expired Token Rejection", passed, f"Status: {res.status_code}, Detail: {res.json().get('detail')}")

    # Test 10: Role differentiation between ADMIN and STAFF
    res_adm = client.get("/api/admin/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    res_stf = client.get("/api/admin/auth/me", headers={"Authorization": f"Bearer {staff_token}"})
    passed = (
        res_adm.status_code == 200
        and res_stf.status_code == 200
        and res_adm.json().get("role") == "ADMIN"
        and res_stf.json().get("role") == "STAFF"
    )
    record(10, "Role Differentiation (ADMIN vs STAFF)", passed, f"Admin Role: {res_adm.json().get('role')}, Staff Role: {res_stf.json().get('role')}")

    # Test 11: Passwords/hashes NEVER exposed in response schemas
    adm_login_json = client.post("/api/admin/auth/login", json={
        "email": "admin@sahkaarsetu.local",
        "password": "SahkaarSetu@Admin2026"
    }).json()
    adm_me_json = client.get("/api/admin/auth/me", headers={"Authorization": f"Bearer {admin_token}"}).json()

    hash_exposed = (
        "password" in adm_login_json
        or "password_hash" in adm_login_json
        or "password" in adm_login_json.get("user", {})
        or "password_hash" in adm_login_json.get("user", {})
        or "password" in adm_me_json
        or "password_hash" in adm_me_json
    )
    record(11, "Password/Hash Non-Exposure", not hash_exposed, "No password or hash leaked in responses")

    # Test 12: Logout endpoint
    res = client.post("/api/admin/auth/logout", headers={"Authorization": f"Bearer {admin_token}"})
    passed = res.status_code == 200 and res.json().get("status") == "ok"
    record(12, "Admin Logout Endpoint", passed, f"Status: {res.status_code}, Response: {res.json()}")

    print("=" * 60)
    failed_tests = [r for r in results if not r[2]]
    if failed_tests:
        print(f"FAILED: {len(failed_tests)} tests failed.")
        sys.exit(1)
    else:
        print(f"SUCCESS: All {len(results)}/12 tests passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    run_tests()
