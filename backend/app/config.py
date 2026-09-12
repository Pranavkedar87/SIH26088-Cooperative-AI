"""
Application configuration loaded from environment variables via pydantic-settings.

All secrets are read from the .env file — never hard-coded.
"""
from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── AI & Voice Providers ──────────────────────────────────────────────
    gemini_api_key: str = ""
    groq_api_key: str = ""

    # ── Bhashini API ──────────────────────────────────────────────────────
    bhashini_user_id: str = ""
    bhashini_api_key: str = ""
    bhashini_pipeline_id: str = ""

    # ── Supabase ──────────────────────────────────────────────────────────
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # ── CORS ──────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins, e.g.:
    # "http://localhost:5173,https://your-app.vercel.app"
    cors_origins: str = "http://localhost:5173,http://localhost:3000,https://pranavkedar87.github.io,*"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── General ───────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"

    # ── Admin Authentication (Phase 2A.1) ──────────────────────────────────
    jwt_secret_key: str = "sahkaarsetu-admin-jwt-secret-key-development-seed-2026"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480  # 8 hours

    # ── Dev / Demo Seed Credentials ────────────────────────────────────────
    dev_admin_email: str = "admin@sahkaarsetu.local"
    dev_admin_password: str = "SahkaarSetu@Admin2026"
    dev_staff_email: str = "staff@sahkaarsetu.local"
    dev_staff_password: str = "SahkaarSetu@Staff2026"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
