"""
Pydantic Schemas for Admin & Operator Authentication (Phase 2A.1).
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    email: str = Field(
        ...,
        description="Operator registered email address.",
        examples=["admin@sahkaarsetu.local"],
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Operator account password.",
    )


class AdminUserResponse(BaseModel):
    id: str = Field(..., description="Unique operator UUID.")
    email: str = Field(..., description="Operator email address.")
    name: str = Field(..., description="Full legal name or display name.")
    role: str = Field(..., description="Operator role: 'ADMIN' or 'STAFF'.")
    assigned_pacs: Optional[str] = Field(
        default=None,
        description="Optional assigned PACS society jurisdiction for STAFF role.",
    )


class AdminLoginResponse(BaseModel):
    access_token: str = Field(..., description="Signed JWT Bearer access token.")
    token_type: str = Field(default="bearer", description="Token scheme type.")
    expires_in: int = Field(..., description="Token lifespan in seconds.")
    user: AdminUserResponse = Field(..., description="Authenticated operator profile.")


class AdminLogoutResponse(BaseModel):
    status: str = Field(default="ok", description="Logout acknowledgment status.")
    message: str = Field(
        default="Logged out successfully. Client-side token removal completed.",
        description="Stateless logout notice.",
    )
