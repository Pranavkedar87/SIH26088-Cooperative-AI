"""
Security & Cryptographic Utilities for SahkaarSetu Admin Authentication.

- Bcrypt salted password hashing and timing-safe verification.
- HMAC-SHA256 signed JWT tokens with expiry enforcement.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt
from app.config import get_settings

logger = logging.getLogger(__name__)


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt with a secure random salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exc:
        logger.warning("Password verification failed with exception: %s", exc)
        return False


def create_access_token(
    subject: str,
    role: str,
    extra_claims: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, int]:
    """
    Create a signed JWT access token.
    Returns (token_string, expires_in_seconds).
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
        expires_in = int(expires_delta.total_seconds())
    else:
        expires_in = settings.jwt_access_token_expire_minutes * 60
        expire = now + timedelta(seconds=expires_in)

    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": "sahkaarsetu-admin-auth",
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.
    Raises jwt.PyJWTError on invalid signature, expiration, or malformed claims.
    """
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        issuer="sahkaarsetu-admin-auth",
        options={"require": ["sub", "exp", "role"]},
    )
