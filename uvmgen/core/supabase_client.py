"""Supabase client initialization for server-side operations."""

from __future__ import annotations

import os
from functools import lru_cache

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY)


def get_public_config() -> dict:
    """Return config safe to expose to the frontend."""
    return {
        "supabase_url": SUPABASE_URL,
        "supabase_anon_key": SUPABASE_ANON_KEY,
        "auth_enabled": is_configured(),
    }
