"""
FastAPI dependency injection.

Swap the provider here (or via config) to change the AI backend.
"""
from __future__ import annotations
from functools import lru_cache
from typing import Any, Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.providers.ai_provider import AIProvider
from app.providers.gemini_provider import GeminiProvider
from app.core.security import decode_access_token
from database.repository import get_user_by_id, get_user_by_email

http_bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def get_ai_provider() -> AIProvider:
    """
    Return the application-wide AI provider singleton.
    Active provider: Gemini (via Google Generative AI SDK).
    """
    return GeminiProvider()


async def get_current_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer_scheme),
) -> dict[str, Any]:
    """
    Validate JWT Bearer token and return the authenticated operator record.
    Raises HTTP 401 if missing, invalid, or expired.
    Raises HTTP 403 if account is deactivated.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user by id or email
    user = get_user_by_id(subject) or get_user_by_email(subject)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Operator account associated with this token was not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operator account has been deactivated.",
        )

    return user


def require_admin_role(allowed_roles: list[str]) -> Callable:
    """
    Factory dependency for verifying the operator holds one of the required roles.
    Example: Depends(require_admin_role(["ADMIN"]))
    """
    async def _role_checker(
        current_user: dict[str, Any] = Depends(get_current_admin_user),
    ) -> dict[str, Any]:
        role = current_user.get("role", "STAFF")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: role '{role}' lacks required permissions.",
            )
        return current_user

    return _role_checker
