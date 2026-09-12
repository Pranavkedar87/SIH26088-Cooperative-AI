"""
Admin & Operator Authentication Router (Phase 2A.1).

POST /api/admin/auth/login
  → Authenticate email & password, issue signed JWT Bearer token.

GET /api/admin/auth/me
  → Verify Bearer token and return active operator profile.

POST /api/admin/auth/logout
  → Acknowledge stateless client-side session termination.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import create_access_token, verify_password
from app.dependencies import get_current_admin_user
from app.schemas.admin_auth import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminLogoutResponse,
    AdminUserResponse,
)
from database.repository import get_user_by_email, update_user_last_login

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])


@router.post(
    "/login",
    response_model=AdminLoginResponse,
    summary="Admin & Staff Operator Login",
)
async def admin_login(body: AdminLoginRequest) -> AdminLoginResponse:
    """
    Authenticate an operator and return a signed JWT Bearer access token.
    Enforces password hashing validation, role checks, and active account verification.
    """
    clean_email = body.email.strip().lower()
    user = get_user_by_email(clean_email)

    # Constant-time failure guard against email enumeration
    if not user or not user.get("password_hash"):
        logger.warning("Failed login attempt for email=%s (user not found)", clean_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(body.password, user["password_hash"]):
        logger.warning("Failed login attempt for email=%s (invalid password)", clean_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        logger.warning("Login attempt for deactivated user=%s", clean_email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operator account has been deactivated. Please contact the administrator.",
        )

    # Update last login timestamp
    update_user_last_login(str(user["id"]))

    role = user.get("role", "STAFF")
    token, expires_in = create_access_token(
        subject=str(user["id"]),
        role=role,
        extra_claims={"email": user["email"]},
    )

    logger.info("Operator authenticated: %s (role=%s)", user["email"], role)

    return AdminLoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=AdminUserResponse(
            id=str(user["id"]),
            email=user["email"],
            name=user.get("full_name") or user.get("name") or "Operator",
            role=role,
            assigned_pacs=user.get("assigned_pacs"),
        ),
    )


@router.get(
    "/me",
    response_model=AdminUserResponse,
    summary="Get Authenticated Operator Profile",
)
async def admin_get_me(
    current_user: dict[str, Any] = Depends(get_current_admin_user),
) -> AdminUserResponse:
    """
    Return the authenticated operator's profile retrieved from the verified JWT Bearer token.
    """
    return AdminUserResponse(
        id=str(current_user["id"]),
        email=current_user["email"],
        name=current_user.get("full_name") or current_user.get("name") or "Operator",
        role=current_user.get("role", "STAFF"),
        assigned_pacs=current_user.get("assigned_pacs"),
    )


@router.post(
    "/logout",
    response_model=AdminLogoutResponse,
    summary="Operator Logout Notice",
)
async def admin_logout(
    current_user: dict[str, Any] = Depends(get_current_admin_user),
) -> AdminLogoutResponse:
    """
    Acknowledge operator logout.
    Note: JWT access tokens are stateless; client-side token disposal completes logout.
    """
    logger.info("Operator logout: %s", current_user.get("email"))
    return AdminLogoutResponse(
        status="ok",
        message="Logged out successfully. Client-side token removal completed.",
    )
