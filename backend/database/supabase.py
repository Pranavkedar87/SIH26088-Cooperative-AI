"""
Supabase client module.

Provides a single, lazily-initialised Supabase client for server-side use.
The service-role key is used so the backend can bypass Row Level Security
for trusted write operations.

Security:
  - SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY come from backend/.env only.
  - These values are NEVER passed to the frontend or included in API responses.
  - The client is None when Supabase is not configured — callers handle this gracefully.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy import so the app starts even if supabase package is not installed.
try:
    from supabase import create_client, Client
    _SUPABASE_AVAILABLE = True
except ImportError:
    _SUPABASE_AVAILABLE = False
    logger.warning("supabase package not installed. Database features disabled.")


@lru_cache(maxsize=1)
def get_supabase_client() -> Optional["Client"]:  # type: ignore[name-defined]
    """
    Return a cached Supabase client using the service-role key.

    Returns None if:
      - supabase package is not installed
      - SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY are not configured

    Callers must handle the None case gracefully.
    """
    if not _SUPABASE_AVAILABLE:
        return None

    from app.config import get_settings
    settings = get_settings()

    url = settings.supabase_url.strip()
    key = settings.supabase_service_role_key.strip()

    if not url or not key:
        logger.warning(
            "Supabase not configured. Set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in backend/.env to enable database features."
        )
        return None

    try:
        client = create_client(url, key)
        logger.info("Supabase client initialised.")
        return client
    except Exception as exc:
        logger.error("Failed to initialise Supabase client: %s", exc)
        return None
