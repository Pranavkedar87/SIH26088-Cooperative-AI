"""
Database repository — simple, reusable functions for chat persistence.

Design principles:
  - Every function is independently safe: it catches its own exceptions.
  - None is returned (not raised) on failure so callers degrade gracefully.
  - No ORM. Raw Supabase client calls only.
  - No fake/seed data. Only real user-generated content is stored.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from database.supabase import get_supabase_client

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _new_id() -> str:
    """Generate a new UUID v4 string."""
    return str(uuid.uuid4())


# ── Sessions ──────────────────────────────────────────────────────────────────

def create_session(language: str) -> Optional[str]:
    """
    Create a new session row and return its UUID.
    Returns None on failure.
    """
    client = get_supabase_client()
    if client is None:
        return None

    session_id = _new_id()
    try:
        client.table("sessions").insert({
            "id": session_id,
            "language": language,
            "user_id": None,
        }).execute()
        logger.info("Session created: %s", session_id)
        return session_id
    except Exception as exc:
        logger.error("Failed to create session: %s", exc)
        return None


# ── Conversations ─────────────────────────────────────────────────────────────

def create_conversation(session_id: str, title: Optional[str] = None) -> Optional[str]:
    """
    Create a new conversation for the given session and return its UUID.
    Returns None on failure.
    """
    client = get_supabase_client()
    if client is None:
        return None

    conversation_id = _new_id()
    try:
        client.table("conversations").insert({
            "id": conversation_id,
            "session_id": session_id,
            "title": title,
        }).execute()
        logger.info("Conversation created: %s (session: %s)", conversation_id, session_id)
        return conversation_id
    except Exception as exc:
        logger.error("Failed to create conversation: %s", exc)
        return None


# ── Messages ──────────────────────────────────────────────────────────────────

def save_message(
    conversation_id: str,
    role: str,
    content: str,
    language: str,
    intent: Optional[str] = None,
) -> Optional[str]:
    """
    Persist a single chat message and return its UUID.
    role must be 'user' or 'assistant'.
    Returns None on failure.
    """
    client = get_supabase_client()
    if client is None:
        return None

    message_id = _new_id()
    try:
        client.table("messages").insert({
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "language": language,
            "intent": intent,
        }).execute()
        logger.debug("Message saved: %s (role=%s)", message_id, role)
        return message_id
    except Exception as exc:
        logger.error("Failed to save message (role=%s): %s", role, exc)
        return None


def get_conversation_messages(conversation_id: str) -> list[dict]:
    """
    Fetch all messages for a conversation in chronological order.
    Returns an empty list on failure.
    """
    client = get_supabase_client()
    if client is None:
        return []

    try:
        result = (
            client.table("messages")
            .select("role, content, language, intent, created_at")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.error(
            "Failed to fetch messages for conversation %s: %s",
            conversation_id,
            exc,
        )
        return []


# ── Grievances ────────────────────────────────────────────────────────────────

def create_grievance(
    conversation_id: Optional[str],
    category: str,
    description: str,
    status: str = "draft",
) -> Optional[str]:
    """
    Create a new grievance record in Supabase.
    Returns grievance UUID string or None on failure.
    """
    client = get_supabase_client()
    if client is None:
        return None

    grievance_id = _new_id()
    try:
        client.table("grievances").insert({
            "id": grievance_id,
            "conversation_id": conversation_id,
            "category": category,
            "description": description,
            "status": status,
        }).execute()
        logger.info("Grievance record created: %s (category=%s)", grievance_id, category)
        return grievance_id
    except Exception as exc:
        logger.error("Failed to create grievance: %s", exc)
        return None


def get_grievance(grievance_id: str) -> Optional[dict]:
    """
    Fetch a grievance record by UUID.
    Returns dict or None if not found/error.
    """
    client = get_supabase_client()
    if client is None:
        return None

    try:
        res = client.table("grievances").select("*").eq("id", grievance_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as exc:
        logger.error("Failed to fetch grievance %s: %s", grievance_id, exc)
        return None


# ── Knowledge Documents ───────────────────────────────────────────────────────

def get_knowledge_documents() -> list[dict]:
    """
    Fetch all knowledge documents stored in database.
    Returns empty list on failure.
    """
    client = get_supabase_client()
    if client is None:
        return []

    try:
        res = client.table("knowledge_documents").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as exc:
        logger.error("Failed to fetch knowledge documents: %s", exc)
        return []

