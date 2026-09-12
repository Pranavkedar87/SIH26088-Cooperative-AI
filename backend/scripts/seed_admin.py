"""
Safe Admin & Staff Account Seeding CLI Script.

Usage:
  python scripts/seed_admin.py --email <email> --password <password> --role ADMIN --name "Admin Name"
  python scripts/seed_admin.py --email <email> --password <password> --role STAFF --name "Staff Name" --pacs "PACS Name"

Safety:
  - Never hardcodes production passwords.
  - Automatically hashes passwords with Bcrypt (cost factor 12).
  - Can read DEV_ADMIN_EMAIL and DEV_ADMIN_PASSWORD from environment.
"""
from __future__ import annotations

import argparse
import os
import sys

# Ensure backend root is in sys.path
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.config import get_settings
from app.core.security import get_password_hash
from database.repository import create_admin_user, get_user_by_email


def main():
    parser = argparse.ArgumentParser(description="Seed an operator account in SahkaarSetu.")
    parser.add_argument("--email", type=str, help="Operator email address.")
    parser.add_argument("--password", type=str, help="Operator password (min 8 chars).")
    parser.add_argument("--role", type=str, choices=["ADMIN", "STAFF"], default="STAFF", help="Role (ADMIN or STAFF).")
    parser.add_argument("--name", type=str, help="Full display name.")
    parser.add_argument("--pacs", type=str, default=None, help="Assigned PACS name (for STAFF role).")

    args = parser.parse_args()
    settings = get_settings()

    email = args.email or (settings.dev_admin_email if args.role == "ADMIN" else settings.dev_staff_email)
    password = args.password or (settings.dev_admin_password if args.role == "ADMIN" else settings.dev_staff_password)
    name = args.name or ("System Administrator" if args.role == "ADMIN" else "PACS Extension Officer")
    role = args.role
    pacs = args.pacs

    if not email or not password:
        print("❌ Error: email and password are required.")
        sys.exit(1)

    if len(password) < 8:
        print("❌ Error: password must be at least 8 characters long.")
        sys.exit(1)

    existing = get_user_by_email(email)
    if existing:
        print(f"⚠️ User with email {email} already exists (ID: {existing.get('id')}). Skipping duplicate creation.")
        return

    pw_hash = get_password_hash(password)
    user_id = create_admin_user(
        email=email,
        password_hash=pw_hash,
        full_name=name,
        role=role,
        assigned_pacs=pacs,
    )

    if user_id:
        print(f"✅ Successfully seeded operator account:")
        print(f"   ID:       {user_id}")
        print(f"   Email:    {email}")
        print(f"   Role:     {role}")
        print(f"   Name:     {name}")
        print(f"   PACS:     {pacs or 'None'}")
    else:
        print("❌ Failed to create user. Check database logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
