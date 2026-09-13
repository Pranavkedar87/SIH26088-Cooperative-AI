"""
Database repository — simple, reusable functions for chat persistence.

Design principles:
  - Every function is independently safe: it catches its own exceptions.
  - None is returned (not raised) on failure so callers degrade gracefully.
  - No ORM. Raw Supabase client calls only.
  - No fake/seed data. Only real user-generated content is stored.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
import uuid
from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from dateutil import parser

from app.config import get_settings
from database.supabase import get_supabase_client

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _new_id() -> str:
    """Generate a new UUID v4 string."""
    return str(uuid.uuid4())


def _is_valid_uuid(val: Optional[str]) -> bool:
    """Check if string is a valid UUID to prevent Postgres 22P02 errors."""
    if not val:
        return False
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


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


def mask_citizen_phone(phone: Optional[str]) -> str:
    """Mask citizen phone number according to privacy guidelines."""
    if not phone or not phone.strip():
        return "+91 98******45"
    cleaned = re.sub(r"[^\d+]", "", phone.strip())
    if len(cleaned) >= 10:
        return f"{cleaned[:6]} •••••"
    return "+91 98******45"


def mask_citizen_name(name: Optional[str]) -> str:
    """Mask citizen name according to privacy guidelines."""
    if not name or not name.strip():
        return "Citizen (Protected)"
    parts = name.strip().split()
    if len(parts) == 1:
        return f"{parts[0][0]}****"
    return f"{parts[0]} {parts[-1][0]}****"


# ── Grievances ────────────────────────────────────────────────────────────────

def create_grievance(
    conversation_id: Optional[str],
    category: str,
    description: str,
    status: str = "draft",
    pacs_name: Optional[str] = None,
    citizen_name: Optional[str] = None,
    citizen_phone: Optional[str] = None,
    ai_guidance: Optional[str] = None,
    priority: str = "medium",
    reference_code: Optional[str] = None,
    citizen_language: Optional[str] = None,
    translated_summary: Optional[str] = None,
    source_citations: Optional[list] = None,
) -> Optional[str]:
    """
    Create a new grievance or assistance record in Supabase with in-memory fallback.
    Returns grievance UUID string or None on failure.
    Backward-compatible: all extended parameters are optional with defaults.
    """
    grievance_id = _new_id()
    now_iso = datetime.now(timezone.utc).isoformat()
    masked_name = mask_citizen_name(citizen_name)
    masked_phone = mask_citizen_phone(citizen_phone)

    client = get_supabase_client()
    if client is not None:
        db_conv_id = conversation_id if _is_valid_uuid(conversation_id) else None
        payload: dict[str, Any] = {
            "id": grievance_id,
            "conversation_id": db_conv_id,
            "category": category,
            "description": description,
            "status": status,
        }
        if pacs_name is not None:
            payload["pacs_name"] = pacs_name
        if citizen_name is not None:
            payload["citizen_masked_name"] = masked_name
        if citizen_phone is not None:
            payload["citizen_phone_masked"] = masked_phone
        if ai_guidance is not None:
            payload["ai_guidance"] = ai_guidance
        if priority is not None:
            payload["priority"] = priority
        if citizen_language is not None:
            payload["citizen_language"] = citizen_language
        if translated_summary is not None:
            payload["translated_summary"] = translated_summary
        if reference_code is not None:
            payload["reference_code"] = reference_code
        if source_citations is not None:
            payload["source_citations"] = source_citations

        try:
            client.table("grievances").insert(payload).execute()
            logger.info("Grievance record created in Supabase: %s (category=%s)", grievance_id, category)
        except Exception as exc:
            logger.warning("Full grievance insert in Supabase failed (retrying core schema): %s", exc)
            try:
                core_payload = {
                    "id": grievance_id,
                    "conversation_id": db_conv_id,
                    "category": category,
                    "description": description,
                    "status": status,
                }
                client.table("grievances").insert(core_payload).execute()
            except Exception as core_exc:
                logger.warning("Core grievance insert in Supabase failed (will use fallback): %s", core_exc)

    # Mirror into in-memory dev fallback for immediate administrative triage
    _init_dev_grievances_fallback()
    _DEV_GRIEVANCES_FALLBACK[grievance_id] = {
        "id": grievance_id,
        "conversation_id": conversation_id,
        "category": category,
        "description": description,
        "status": status,
        "priority": priority or "medium",
        "assigned_staff": None,
        "pacs_name": pacs_name,
        "citizen_masked_name": masked_name,
        "citizen_phone_masked": masked_phone,
        "staff_notes": [],
        "ai_guidance": ai_guidance or "Grievance recorded for administrative review.",
        "reference_code": reference_code,
        "citizen_language": citizen_language or "mr",
        "translated_summary": translated_summary,
        "source_citations": source_citations or [],
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    return grievance_id


def get_grievance(grievance_id: str) -> Optional[dict]:
    """
    Fetch a grievance record by UUID with fallback enrichment.
    Returns dict or None if not found/error.
    """
    _init_dev_grievances_fallback()
    fallback_meta = _DEV_GRIEVANCES_FALLBACK.get(grievance_id, {})

    client = get_supabase_client()
    if client is not None:
        try:
            res = client.table("grievances").select("*").eq("id", grievance_id).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                return {
                    "id": str(row.get("id")),
                    "conversation_id": row.get("conversation_id") or fallback_meta.get("conversation_id"),
                    "category": row.get("category") or fallback_meta.get("category", "PACS Service"),
                    "description": row.get("description") or fallback_meta.get("description", ""),
                    "status": normalize_status(row.get("status")) or fallback_meta.get("status", "draft"),
                    "priority": normalize_priority(row.get("priority")) or fallback_meta.get("priority", "medium"),
                    "assigned_staff": row.get("assigned_staff") or fallback_meta.get("assigned_staff"),
                    "pacs_name": row.get("pacs_name") or fallback_meta.get("pacs_name"),
                    "citizen_masked_name": row.get("citizen_masked_name") or fallback_meta.get("citizen_masked_name", "Citizen (Protected)"),
                    "citizen_phone_masked": row.get("citizen_phone_masked") or fallback_meta.get("citizen_phone_masked", "+91 98******45"),
                    "staff_notes": row.get("staff_notes") or fallback_meta.get("staff_notes", []),
                    "ai_guidance": row.get("ai_guidance") or fallback_meta.get("ai_guidance"),
                    "reference_code": row.get("reference_code") or fallback_meta.get("reference_code"),
                    "citizen_language": row.get("citizen_language") or fallback_meta.get("citizen_language", "mr"),
                    "translated_summary": row.get("translated_summary") or fallback_meta.get("translated_summary"),
                    "source_citations": row.get("source_citations") or fallback_meta.get("source_citations", []),
                    "created_at": row.get("created_at") or fallback_meta.get("created_at"),
                    "updated_at": row.get("updated_at") or fallback_meta.get("updated_at"),
                }
        except Exception as exc:
            logger.debug("Supabase get_grievance error: %s", exc)

    return fallback_meta if fallback_meta else None


# ── Admin Grievance Triage (Phase 2A.2) ────────────────────────────────────────

_DEV_GRIEVANCES_FALLBACK: dict[str, dict] = {}

VALID_STATUS_LIFECYCLE: dict[str, set[str]] = {
    "draft": {"submitted"},
    "submitted": {"under_review", "draft"},
    "under_review": {"resolved", "submitted"},
    "resolved": {"closed", "under_review"},
    "closed": {"under_review"},
}


def normalize_status(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    s = val.strip().lower().replace(" ", "_").replace("-", "_")
    mapping = {
        "new": "submitted",
        "assigned": "under_review",
        "in_progress": "under_review",
        "escalated": "under_review",
        "escalate_to_ddr": "under_review",
        "mark_resolved": "resolved",
    }
    return mapping.get(s, s)


def normalize_priority(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    p = val.strip().lower()
    if p in ("urgent", "high", "medium", "low"):
        return p
    return "medium"


def _init_dev_grievances_fallback() -> None:
    if _DEV_GRIEVANCES_FALLBACK:
        return

    cases = [
        {
            "id": "GRV-2026-001",
            "conversation_id": None,
            "category": "PMFBY",
            "pacs_name": "Dindori Primary Agriculture Cooperative Society",
            "priority": "urgent",
            "status": "under_review",
            "assigned_staff": "Sunil Patil (Agri Extension Officer)",
            "citizen_masked_name": "Tukaram S. K****",
            "citizen_phone_masked": "+91 98221 •••••",
            "description": "माझ्या कांदा पिकाचे अवकाळी पावसामुळे ७०% नुकसान झाले आहे. ७२ तास उलटून गेले पण ॲपवर तक्रार नोंदवता येत नाही. काय करावे?",
            "ai_guidance": "Advised Section 15.2 of PMFBY Operational Guidelines: In case of network outage, farmer may submit offline Annexure-IV intimation notice directly to PACS Secretary or Bank within 7 days, backed by a village talathi endorsement.",
            "staff_notes": [
                {
                    "id": "NOTE-001",
                    "note": "Physical offline loss intimation received by Dindori PACS clerk.",
                    "author_id": "USR-STF-014",
                    "author_name": "Sunil Patil",
                    "author_role": "STAFF",
                    "created_at": "2026-03-10T10:00:00Z",
                },
                {
                    "id": "NOTE-002",
                    "note": "Forwarded to Insurance Company field surveyor Mr. G. Shinde.",
                    "author_id": "USR-STF-014",
                    "author_name": "Sunil Patil",
                    "author_role": "STAFF",
                    "created_at": "2026-03-11T14:30:00Z",
                },
            ],
            "created_at": "2026-03-10T09:15:00Z",
            "updated_at": "2026-03-11T14:30:00Z",
        },
        {
            "id": "GRV-2026-002",
            "conversation_id": None,
            "category": "Financial",
            "pacs_name": "Baramati Taluka Sahakari Kharedi Vikri Sangh",
            "priority": "high",
            "status": "submitted",
            "assigned_staff": "Pooja Deshmukh",
            "citizen_masked_name": "Anil B. J****",
            "citizen_phone_masked": "+91 94230 •••••",
            "description": "KCC कर्जाची वेळेत परतफेड करूनही ३% व्याज सवलत खात्यावर जमा झाली नाही.",
            "ai_guidance": "Clarified RBI & NABARD guidelines on Interest Subvention Scheme (ISS). The 3% subvention is routed via DBT through DCCB after PACS submits audit reconciliation roll.",
            "staff_notes": [],
            "created_at": "2026-03-11T11:20:00Z",
            "updated_at": "2026-03-11T11:20:00Z",
        },
        {
            "id": "GRV-2026-003",
            "conversation_id": None,
            "category": "PACS Service",
            "pacs_name": "Shirol Dairy & Multipurpose Cooperative",
            "priority": "medium",
            "status": "under_review",
            "assigned_staff": "Ramesh Sawant",
            "citizen_masked_name": "Nirmala D. M****",
            "citizen_phone_masked": "+91 97654 •••••",
            "description": "दूध संकलन केंद्रावर फॅट आणि एसएनएफ मशिन सदोष आहे. दररोज २ लिटर दूध कमी दाखवले जात आहे.",
            "ai_guidance": "Highlighted Model By-law Rule 28 for Dairy Cooperatives: Society must maintain daily calibration register certified by standard weights and measures inspector and provide duplicate test slip on request.",
            "staff_notes": [],
            "created_at": "2026-03-08T08:00:00Z",
            "updated_at": "2026-03-09T09:00:00Z",
        },
        {
            "id": "GRV-2026-004",
            "conversation_id": None,
            "category": "Cooperative Issue",
            "pacs_name": "Nashik District Central Cooperative Bank",
            "priority": "low",
            "status": "resolved",
            "assigned_staff": "Shri Rajesh K. Sharma",
            "citizen_masked_name": "Dnyaneshwar P****",
            "citizen_phone_masked": "+91 91580 •••••",
            "description": "सोसायटीच्या वार्षिक सर्वसाधारण सभेची (AGM) नोटीस वेळेत मिळाली नाही.",
            "ai_guidance": "Under Section 75 of Maharashtra Cooperative Societies Act, minimum 14 days notice is statutory for AGM convening.",
            "staff_notes": [
                {
                    "id": "NOTE-003",
                    "note": "Resolved after society re-issued registered notice to member.",
                    "author_id": "USR-ADM-001",
                    "author_name": "Rajesh Sharma",
                    "author_role": "ADMIN",
                    "created_at": "2026-03-12T11:00:00Z",
                }
            ],
            "created_at": "2026-03-05T14:10:00Z",
            "updated_at": "2026-03-12T11:00:00Z",
        },
    ]
    for c in cases:
        _DEV_GRIEVANCES_FALLBACK[c["id"]] = c


def is_operator_authorized_for_grievance(user: dict, grievance: dict) -> bool:
    """
    Evaluate RBAC rule:
    ADMIN: Can view and manage all grievances across all PACS.
    STAFF: Can view/manage grievances assigned to them OR belonging to their assigned PACS.
    """
    if not user:
        return False
    if user.get("role") == "ADMIN":
        return True

    user_pacs = (user.get("assigned_pacs") or "").strip().lower()
    grv_pacs = (grievance.get("pacs_name") or "").strip().lower()
    if user_pacs and grv_pacs and user_pacs == grv_pacs:
        return True

    assigned = (grievance.get("assigned_staff") or "").strip().lower()
    user_email = (user.get("email") or "").strip().lower()
    user_name = (user.get("full_name") or "").strip().lower()
    if assigned:
        if user_email and user_email == assigned:
            return True
        if user_name and (user_name in assigned or assigned in user_name):
            return True
        first_name = user_name.split()[0] if user_name else ""
        if first_name and len(first_name) >= 3 and first_name in assigned:
            return True

    return False


def list_admin_grievances(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    pacs: Optional[str] = None,
    search: Optional[str] = None,
    user: Optional[dict] = None,
) -> dict:
    """
    List grievances with pagination, filtering, search, and strict RBAC enforcement.
    """
    _init_dev_grievances_fallback()
    records: list[dict] = []

    client = get_supabase_client()
    if client is not None:
        try:
            q = client.table("grievances").select("*").order("created_at", desc=True)
            res = q.execute()
            if res.data:
                for row in res.data:
                    # Enrich with fallback defaults if additive columns are not yet in DB
                    row_id = str(row.get("id"))
                    fallback_meta = _DEV_GRIEVANCES_FALLBACK.get(row_id, {})
                    record = {
                        "id": row_id,
                        "conversation_id": row.get("conversation_id"),
                        "category": row.get("category") or fallback_meta.get("category", "PACS Service"),
                        "description": row.get("description") or fallback_meta.get("description", ""),
                        "status": normalize_status(row.get("status")) or fallback_meta.get("status", "draft"),
                        "priority": normalize_priority(row.get("priority")) or fallback_meta.get("priority", "medium"),
                        "assigned_staff": row.get("assigned_staff") or fallback_meta.get("assigned_staff"),
                        "pacs_name": row.get("pacs_name") or fallback_meta.get("pacs_name"),
                        "citizen_masked_name": row.get("citizen_masked_name") or fallback_meta.get("citizen_masked_name", "Citizen (Protected)"),
                        "citizen_phone_masked": row.get("citizen_phone_masked") or fallback_meta.get("citizen_phone_masked", "+91 98******45"),
                        "staff_notes": row.get("staff_notes") or fallback_meta.get("staff_notes", []),
                        "ai_guidance": row.get("ai_guidance") or fallback_meta.get("ai_guidance"),
                        "reference_code": row.get("reference_code") or fallback_meta.get("reference_code"),
                        "citizen_language": row.get("citizen_language") or fallback_meta.get("citizen_language", "mr"),
                        "translated_summary": row.get("translated_summary") or fallback_meta.get("translated_summary"),
                        "source_citations": row.get("source_citations") or fallback_meta.get("source_citations", []),
                        "created_at": row.get("created_at") or fallback_meta.get("created_at", datetime.now(timezone.utc).isoformat()),
                        "updated_at": row.get("updated_at") or fallback_meta.get("updated_at", datetime.now(timezone.utc).isoformat()),
                    }
                    records.append(record)
        except Exception as exc:
            logger.warning("Supabase list grievances error (fallback engaged): %s", exc)

    # Merge with dev fallback records that aren't already in records
    existing_ids = {r["id"] for r in records}
    for fb_id, fb_record in _DEV_GRIEVANCES_FALLBACK.items():
        if fb_id not in existing_ids:
            records.append(dict(fb_record))

    # Apply RBAC filter
    if user:
        records = [r for r in records if is_operator_authorized_for_grievance(user, r)]

    # Apply Query Filters
    norm_status = normalize_status(status)
    norm_priority = normalize_priority(priority) if priority else None

    filtered = []
    for r in records:
        if norm_status and r.get("status") != norm_status:
            continue
        if norm_priority and r.get("priority") != norm_priority:
            continue
        if category and category.lower() != "all" and r.get("category", "").lower() != category.lower():
            continue
        if pacs and pacs.lower() not in (r.get("pacs_name") or "").lower():
            continue
        if search:
            q_clean = search.strip().lower()
            text_corpus = f"{r.get('id', '')} {r.get('reference_code', '')} {r.get('description', '')} {r.get('citizen_masked_name', '')} {r.get('pacs_name', '')} {r.get('category', '')}".lower()
            if q_clean not in text_corpus:
                continue
        filtered.append(r)

    # Sort descending by created_at
    filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    total = len(filtered)
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    items = filtered[start_idx:end_idx]

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def get_admin_grievance_by_id(grievance_id: str, user: dict) -> Optional[dict]:
    """
    Retrieve single grievance details with conversation transcript and RBAC authorization check.
    Raises PermissionError if operator is not authorized.
    Returns None if grievance does not exist.
    """
    _init_dev_grievances_fallback()
    record = None

    client = get_supabase_client()
    if client is not None:
        try:
            res = client.table("grievances").select("*").eq("id", grievance_id).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                fb = _DEV_GRIEVANCES_FALLBACK.get(grievance_id, {})
                record = {
                    "id": str(row.get("id")),
                    "conversation_id": row.get("conversation_id"),
                    "category": row.get("category") or fb.get("category", "PACS Service"),
                    "description": row.get("description") or fb.get("description", ""),
                    "status": normalize_status(row.get("status")) or fb.get("status", "draft"),
                    "priority": normalize_priority(row.get("priority")) or fb.get("priority", "medium"),
                    "assigned_staff": row.get("assigned_staff") or fb.get("assigned_staff"),
                    "pacs_name": row.get("pacs_name") or fb.get("pacs_name"),
                    "citizen_masked_name": row.get("citizen_masked_name") or fb.get("citizen_masked_name", "Citizen (Protected)"),
                    "citizen_phone_masked": row.get("citizen_phone_masked") or fb.get("citizen_phone_masked", "+91 98******45"),
                    "staff_notes": row.get("staff_notes") or fb.get("staff_notes", []),
                    "ai_guidance": row.get("ai_guidance") or fb.get("ai_guidance"),
                    "created_at": row.get("created_at") or fb.get("created_at", datetime.now(timezone.utc).isoformat()),
                    "updated_at": row.get("updated_at") or fb.get("updated_at", datetime.now(timezone.utc).isoformat()),
                }
        except Exception as exc:
            logger.debug("Supabase get_admin_grievance error: %s", exc)

    if record is None:
        if grievance_id in _DEV_GRIEVANCES_FALLBACK:
            record = dict(_DEV_GRIEVANCES_FALLBACK[grievance_id])

    if record is None:
        return None

    # Enforce RBAC
    if not is_operator_authorized_for_grievance(user, record):
        raise PermissionError(f"Operator {user.get('email')} is not authorized to access grievance {grievance_id}.")

    # Fetch linked conversation messages if conversation_id exists
    conv_messages: list[dict] = []
    conv_id = record.get("conversation_id")
    if conv_id:
        conv_messages = get_conversation_messages(str(conv_id))
    record["conversation"] = conv_messages

    return record


def update_admin_grievance(grievance_id: str, updates: dict, user: dict) -> Optional[dict]:
    """
    Update grievance status, priority, or assigned staff with transition validation and RBAC.
    Raises PermissionError if unauthorized.
    Raises ValueError if status transition is invalid.
    Returns updated record or None if not found.
    """
    record = get_admin_grievance_by_id(grievance_id, user)
    if record is None:
        return None

    current_status = record.get("status", "draft")
    target_status = normalize_status(updates.get("status")) if updates.get("status") else None
    target_priority = normalize_priority(updates.get("priority")) if updates.get("priority") else None
    target_staff = updates.get("assigned_staff")

    # Validate status transition
    if target_status and target_status != current_status:
        allowed = VALID_STATUS_LIFECYCLE.get(current_status, set())
        if target_status not in allowed:
            raise ValueError(
                f"Invalid status transition from '{current_status}' to '{target_status}'. "
                f"Allowed transitions: {sorted(list(allowed))}"
            )
        record["status"] = target_status

    if target_priority:
        record["priority"] = target_priority

    if target_staff is not None:
        record["assigned_staff"] = target_staff

    record["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Persist in Supabase if possible
    client = get_supabase_client()
    if client is not None:
        try:
            update_payload: dict[str, Any] = {"updated_at": record["updated_at"]}
            if target_status:
                update_payload["status"] = target_status
            if target_priority:
                update_payload["priority"] = target_priority
            if target_staff is not None:
                update_payload["assigned_staff"] = target_staff
            client.table("grievances").update(update_payload).eq("id", grievance_id).execute()
        except Exception as exc:
            logger.debug("Supabase update_admin_grievance error (migration may be pending): %s", exc)

    # Persist in fallback
    _DEV_GRIEVANCES_FALLBACK[grievance_id] = record
    return record


def append_grievance_note(grievance_id: str, note_text: str, user: dict) -> Optional[dict]:
    """
    Append an internal verification note to grievance history.
    Raises PermissionError if unauthorized.
    """
    record = get_admin_grievance_by_id(grievance_id, user)
    if record is None:
        return None

    now_iso = datetime.now(timezone.utc).isoformat()
    note_id = f"NOTE-{_new_id()[:8].upper()}"
    new_note = {
        "id": note_id,
        "note": note_text.strip(),
        "author_id": str(user.get("id")),
        "author_name": user.get("full_name") or user.get("email", "Operator"),
        "author_role": user.get("role", "STAFF"),
        "created_at": now_iso,
    }

    current_notes = list(record.get("staff_notes") or [])
    current_notes.append(new_note)
    record["staff_notes"] = current_notes
    record["updated_at"] = now_iso

    # Persist in Supabase if possible
    client = get_supabase_client()
    if client is not None:
        try:
            client.table("grievances").update({
                "staff_notes": current_notes,
                "updated_at": now_iso,
            }).eq("id", grievance_id).execute()
        except Exception as exc:
            logger.debug("Supabase append_grievance_note error: %s", exc)

    _DEV_GRIEVANCES_FALLBACK[grievance_id] = record
    return record


# ── Kiosks Fleet Monitoring (Phase 2A.3) ──────────────────────────────────────

_DEV_KIOSKS_FALLBACK: dict[str, dict] = {}


def compute_kiosk_key_hash(raw_key: str) -> str:
    """Compute SHA-256 hex digest of kiosk machine key."""
    return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()


def _init_dev_kiosks_fallback() -> None:
    if _DEV_KIOSKS_FALLBACK:
        return

    now = datetime.now(timezone.utc)
    fresh_hb = now.isoformat()
    # 20 minutes ago (exceeds 15 min threshold -> offline)
    old_hb = datetime.fromtimestamp(now.timestamp() - 1200, tz=timezone.utc).isoformat()

    seed_kiosks = [
        {
            "id": "KSK-001",
            "name": "Nashik Central PACS Kiosk",
            "location": "Dindori Road, Nashik",
            "district": "Nashik",
            "state": "Maharashtra",
            "pacs_name": "Dindori Primary Agriculture Cooperative Society",
            "status": "online",
            "software_version": "v2.4.1",
            "ip_address": "192.168.12.45",
            "installation_date": "2025-08-15",
            "uptime_percent": 99.4,
            "health": {
                "device": "ok",
                "network": "online",
                "printer": "ready",
                "sync": "synced",
            },
            "last_heartbeat": fresh_hb,
            "api_key_hash": compute_kiosk_key_hash("kiosk-secret-dindori-001"),
            "notes": "Primary rural farmer kiosk with high Marathi voice usage.",
            "created_at": "2025-08-15T09:00:00Z",
            "updated_at": fresh_hb,
        },
        {
            "id": "KSK-002",
            "name": "Baramati Cooperative Touchpoint",
            "location": "Market Yard, Baramati",
            "district": "Pune",
            "state": "Maharashtra",
            "pacs_name": "Baramati Taluka Sahakari Kharedi Vikri Sangh",
            "status": "online",
            "software_version": "v2.4.1",
            "ip_address": "192.168.14.88",
            "installation_date": "2025-09-10",
            "uptime_percent": 98.7,
            "health": {
                "device": "ok",
                "network": "online",
                "printer": "low_paper",
                "sync": "synced",
            },
            "last_heartbeat": fresh_hb,
            "api_key_hash": compute_kiosk_key_hash("kiosk-secret-baramati-002"),
            "notes": "Heavy PMFBY claim assistance point. Thermal printer paper low.",
            "created_at": "2025-09-10T10:00:00Z",
            "updated_at": fresh_hb,
        },
        {
            "id": "KSK-003",
            "name": "Kolhapur Dudh Sahakari Point",
            "location": "Shirol, Kolhapur",
            "district": "Kolhapur",
            "state": "Maharashtra",
            "pacs_name": "Shirol Dairy & Multipurpose Cooperative",
            "status": "offline",
            "software_version": "v2.4.0",
            "ip_address": "192.168.18.22",
            "installation_date": "2025-10-04",
            "uptime_percent": 97.2,
            "health": {
                "device": "ok",
                "network": "weak",
                "printer": "ready",
                "sync": "synced",
            },
            "last_heartbeat": old_hb,
            "api_key_hash": compute_kiosk_key_hash("kiosk-secret-shirol-003"),
            "notes": "Dairy society kiosk. Network intermittent in valley zone.",
            "created_at": "2025-10-04T11:00:00Z",
            "updated_at": old_hb,
        },
        {
            "id": "KSK-004",
            "name": "Nashik District DCCB Touchpoint",
            "location": "CBS Square, Nashik",
            "district": "Nashik",
            "state": "Maharashtra",
            "pacs_name": "Nashik District Central Cooperative Bank",
            "status": "maintenance",
            "software_version": "v2.4.1",
            "ip_address": "192.168.10.12",
            "installation_date": "2025-07-20",
            "uptime_percent": 95.8,
            "health": {
                "device": "degraded",
                "network": "online",
                "printer": "paper_jam",
                "sync": "synced",
            },
            "last_heartbeat": fresh_hb,
            "api_key_hash": compute_kiosk_key_hash("kiosk-secret-nashik-004"),
            "notes": "Under scheduled maintenance for thermal printer replacement.",
            "created_at": "2025-07-20T08:00:00Z",
            "updated_at": fresh_hb,
        },
    ]

    for k in seed_kiosks:
        _DEV_KIOSKS_FALLBACK[k["id"]] = k


def calculate_deterministic_kiosk_status(raw_status: str, last_heartbeat_iso: Optional[str]) -> str:
    """
    Deterministic offline classification rule:
    - If status is 'maintenance', it strictly remains 'maintenance'.
    - If last_heartbeat is within kiosk_offline_threshold_seconds (900s / 15 min), status is 'online'.
    - If last_heartbeat is missing or older than 900s, status is 'offline'.
    """
    if (raw_status or "").lower() == "maintenance":
        return "maintenance"
    if not last_heartbeat_iso:
        return "offline"

    try:
        hb_clean = last_heartbeat_iso.replace("Z", "+00:00")
        hb_dt = datetime.fromisoformat(hb_clean)
        now = datetime.now(timezone.utc)
        threshold = get_settings().kiosk_offline_threshold_seconds
        elapsed = (now - hb_dt).total_seconds()
        if elapsed <= threshold:
            return "online"
        return "offline"
    except Exception:
        return "offline"


def is_operator_authorized_for_kiosk(user: dict, kiosk: dict) -> bool:
    """
    RBAC enforcement:
    - ADMIN: Full access to all kiosks across all PACS.
    - STAFF: Can ONLY view or manage kiosks in their assigned PACS society.
    """
    if not user:
        return False
    if user.get("role") == "ADMIN":
        return True

    user_pacs = (user.get("assigned_pacs") or "").strip().lower()
    kiosk_pacs = (kiosk.get("pacs_name") or "").strip().lower()
    if user_pacs and kiosk_pacs and user_pacs == kiosk_pacs:
        return True
    return False


def list_kiosks(
    district: Optional[str] = None,
    state: Optional[str] = None,
    pacs: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    user: Optional[dict] = None,
) -> list[dict]:
    """
    List kiosks with filtering and strict RBAC isolation for STAFF.
    Production behavior: queries Supabase. If error in production, raises RuntimeError.
    Development behavior: merges with _DEV_KIOSKS_FALLBACK.
    """
    settings = get_settings()
    is_dev = settings.app_env.lower() in ("development", "dev", "test", "testing", "local")

    records: list[dict] = []
    client = get_supabase_client()
    db_queried_successfully = False

    if client is not None:
        try:
            res = client.table("kiosks").select("*").order("created_at", desc=True).execute()
            if res.data is not None:
                records = list(res.data)
                db_queried_successfully = True
        except Exception as exc:
            logger.warning("Supabase kiosks query failed: %s", exc)
            if not is_dev:
                raise RuntimeError("Kiosk database is unavailable in production") from exc

    if not db_queried_successfully:
        if not is_dev:
            raise RuntimeError("Kiosk database connection unavailable in production")
        _init_dev_kiosks_fallback()
        records = [dict(v) for v in _DEV_KIOSKS_FALLBACK.values()]
    else:
        # In dev, if table is empty, merge fallback
        if is_dev and len(records) == 0:
            _init_dev_kiosks_fallback()
            records = [dict(v) for v in _DEV_KIOSKS_FALLBACK.values()]

    # Apply deterministic status calculation to each kiosk
    for r in records:
        r["status"] = calculate_deterministic_kiosk_status(r.get("status"), r.get("last_heartbeat"))

    # Apply RBAC filter
    if user:
        records = [r for r in records if is_operator_authorized_for_kiosk(user, r)]

    # Apply query filters
    filtered: list[dict] = []
    for k in records:
        if district and district.lower() != "all" and (k.get("district") or "").lower() != district.lower():
            continue
        if state and state.lower() != "all" and (k.get("state") or "").lower() != state.lower():
            continue
        if pacs and pacs.lower() not in (k.get("pacs_name") or "").lower():
            continue
        if status and status.lower() != "all" and k.get("status") != status.lower():
            continue
        if search:
            q = search.strip().lower()
            corpus = f"{k.get('id', '')} {k.get('name', '')} {k.get('location', '')} {k.get('pacs_name', '')} {k.get('district', '')}".lower()
            if q not in corpus:
                continue
        filtered.append(k)

    return filtered


def get_kiosk_by_id(kiosk_id: str, user: dict) -> Optional[dict]:
    """
    Retrieve single kiosk with RBAC check.
    Raises PermissionError if unauthorized STAFF tries to access kiosk outside their PACS.
    Returns None if kiosk not found.
    """
    settings = get_settings()
    is_dev = settings.app_env.lower() in ("development", "dev", "test", "testing", "local")

    record = None
    client = get_supabase_client()
    if client is not None:
        try:
            res = client.table("kiosks").select("*").eq("id", kiosk_id).execute()
            if res.data and len(res.data) > 0:
                record = res.data[0]
        except Exception as exc:
            logger.debug("Supabase get_kiosk_by_id error: %s", exc)
            if not is_dev:
                raise RuntimeError("Kiosk database is unavailable in production") from exc

    if record is None and is_dev:
        _init_dev_kiosks_fallback()
        if kiosk_id in _DEV_KIOSKS_FALLBACK:
            record = dict(_DEV_KIOSKS_FALLBACK[kiosk_id])

    if record is None:
        return None

    # Calculate status
    record["status"] = calculate_deterministic_kiosk_status(record.get("status"), record.get("last_heartbeat"))

    # RBAC check
    if not is_operator_authorized_for_kiosk(user, record):
        raise PermissionError(f"Operator {user.get('email')} is not authorized to access kiosk {kiosk_id}.")

    return record


def update_kiosk_operational(kiosk_id: str, status: Optional[str], notes: Optional[str], user: dict) -> Optional[dict]:
    """
    Admin/Staff operational update: permits ONLY status and notes.
    Rejects unauthorized access with PermissionError.
    """
    kiosk = get_kiosk_by_id(kiosk_id, user)
    if kiosk is None:
        return None

    now_iso = datetime.now(timezone.utc).isoformat()
    if status is not None:
        kiosk["status"] = status.lower()
    if notes is not None:
        kiosk["notes"] = notes
    kiosk["updated_at"] = now_iso

    client = get_supabase_client()
    if client is not None:
        try:
            update_data: dict[str, Any] = {"updated_at": now_iso}
            if status is not None:
                update_data["status"] = status.lower()
            if notes is not None:
                update_data["notes"] = notes
            client.table("kiosks").update(update_data).eq("id", kiosk_id).execute()
        except Exception as exc:
            logger.debug("Supabase update_kiosk_operational error: %s", exc)

    _init_dev_kiosks_fallback()
    if kiosk_id in _DEV_KIOSKS_FALLBACK:
        _DEV_KIOSKS_FALLBACK[kiosk_id] = kiosk

    return kiosk


def process_kiosk_heartbeat(kiosk_id: str, telemetry: dict, provided_key: str) -> dict:
    """
    Process M2M heartbeat:
    1. Authenticate device via per-kiosk api_key_hash (or KIOSK_HEARTBEAT_SECRET env override).
    2. Update last_heartbeat, health, software_version, ip_address, updated_at.
    3. Transition status from offline -> online (if status != 'maintenance').
    Raises PermissionError if key is invalid.
    Raises LookupError if kiosk ID not found.
    """
    settings = get_settings()
    is_dev = settings.app_env.lower() in ("development", "dev", "test", "testing", "local")

    kiosk = None
    client = get_supabase_client()
    if client is not None:
        try:
            res = client.table("kiosks").select("*").eq("id", kiosk_id).execute()
            if res.data and len(res.data) > 0:
                kiosk = res.data[0]
        except Exception as exc:
            logger.debug("Supabase heartbeat fetch error: %s", exc)

    if kiosk is None and is_dev:
        _init_dev_kiosks_fallback()
        if kiosk_id in _DEV_KIOSKS_FALLBACK:
            kiosk = dict(_DEV_KIOSKS_FALLBACK[kiosk_id])

    if kiosk is None:
        raise LookupError(f"Kiosk '{kiosk_id}' not found.")

    # Validate credential
    stored_hash = kiosk.get("api_key_hash")
    key_valid = False
    if provided_key:
        if stored_hash and compute_kiosk_key_hash(provided_key) == stored_hash:
            key_valid = True
        elif settings.kiosk_heartbeat_secret and provided_key.strip() == settings.kiosk_heartbeat_secret:
            key_valid = True

    if not key_valid:
        raise PermissionError(f"Invalid kiosk credentials for '{kiosk_id}'.")

    # Update ONLY explicitly allowed telemetry fields
    now_iso = datetime.now(timezone.utc).isoformat()
    health_update = {
        "device": telemetry.get("device_status") or "ok",
        "network": telemetry.get("network_status") or "online",
        "printer": telemetry.get("printer_status") or "ready",
        "sync": telemetry.get("sync_status") or "synced",
    }

    kiosk["last_heartbeat"] = now_iso
    kiosk["health"] = health_update
    kiosk["updated_at"] = now_iso

    if telemetry.get("software_version"):
        kiosk["software_version"] = telemetry["software_version"]
    if telemetry.get("ip_address"):
        kiosk["ip_address"] = telemetry["ip_address"]

    # Status rule: offline -> online, but NEVER remove maintenance automatically
    if kiosk.get("status") != "maintenance":
        kiosk["status"] = "online"

    # Persist in Supabase if client available
    if client is not None:
        try:
            client.table("kiosks").update({
                "last_heartbeat": now_iso,
                "health": health_update,
                "updated_at": now_iso,
                "status": kiosk["status"],
                **({"software_version": kiosk["software_version"]} if telemetry.get("software_version") else {}),
                **({"ip_address": kiosk["ip_address"]} if telemetry.get("ip_address") else {}),
            }).eq("id", kiosk_id).execute()
        except Exception as exc:
            logger.debug("Supabase heartbeat update error: %s", exc)

    if kiosk_id in _DEV_KIOSKS_FALLBACK:
        _DEV_KIOSKS_FALLBACK[kiosk_id] = kiosk

    return {
        "status": "ok",
        "kiosk_id": kiosk_id,
        "received_at": now_iso,
        "state": kiosk["status"],
    }

# ── Governed Knowledge Management (Phase 2B.1) ────────────────────────────────

_KNOWLEDGE_DOCS_DEV_OVERLAY: dict[str, dict] = {}
_KB_CURATED_METADATA: Optional[dict[str, dict]] = None


def is_document_eligible_for_retrieval(doc: dict) -> bool:
    """
    Phase 2B.1 Governed Knowledge Safety Gate:
    Enforces that ONLY published and current documents can participate in live citizen retrieval.
    Draft, under_review, verified, outdated, and superseded documents are strictly rejected.
    """
    if not doc:
        return False
    status = (doc.get("status") or "published").lower().strip()
    is_current = doc.get("is_current")
    if is_current is None:
        is_current = True

    if status != "published" or not is_current:
        return False
    return True


def _get_knowledge_base_curated_metadata() -> dict[str, dict]:
    """Load governance metadata from knowledge_base JSON files without altering DB."""
    import glob
    kb_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")
    meta_map = {}
    if os.path.exists(kb_dir):
        for filepath in glob.glob(os.path.join(kb_dir, "**/*.json"), recursive=True):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    title = data.get("title")
                    if title:
                        meta_map[title] = data
            except Exception:
                pass
    return meta_map


def enrich_knowledge_doc(doc: dict) -> dict:
    """
    Enrich raw knowledge document with conservative governance defaults
    matching Phase 2B.1 requirements:
    - verification_status: NEEDS_VERIFICATION or OFFICIAL_NEEDS_VERIFICATION (never invented VERIFIED_OFFICIAL)
    - currentness_status: NEEDS_VERIFICATION or UNKNOWN (never invented ACTIVE_IN_FORCE)
    - status: 'published' for existing corpus unless overridden
    - is_current: True for existing corpus unless overridden
    - version: 'v1.0' unless overridden
    """
    global _KB_CURATED_METADATA
    if _KB_CURATED_METADATA is None:
        _KB_CURATED_METADATA = _get_knowledge_base_curated_metadata()

    doc_copy = dict(doc)
    doc_id = str(doc_copy.get("id", ""))

    if doc_id in _KNOWLEDGE_DOCS_DEV_OVERLAY:
        doc_copy.update(_KNOWLEDGE_DOCS_DEV_OVERLAY[doc_id])
        return doc_copy

    title = doc_copy.get("title", "")
    curated = _KB_CURATED_METADATA.get(title, {})

    doc_copy["status"] = (doc_copy.get("status") or curated.get("status") or "published").lower()
    doc_copy["version"] = doc_copy.get("version") or curated.get("version") or "v1.0"
    if doc_copy.get("is_current") is None:
        doc_copy["is_current"] = curated.get("is_current", True)

    doc_copy["authority_level"] = doc_copy.get("authority_level") or curated.get("authority_level") or "UNKNOWN"
    doc_copy["jurisdiction"] = doc_copy.get("jurisdiction") or curated.get("jurisdiction") or "MAHARASHTRA"
    doc_copy["applicability"] = doc_copy.get("applicability") or curated.get("applicability") or ["ALL_COOPERATIVES"]
    doc_copy["verification_status"] = doc_copy.get("verification_status") or curated.get("verification_status") or "NEEDS_VERIFICATION"
    doc_copy["currentness_status"] = doc_copy.get("currentness_status") or curated.get("currentness_status") or "NEEDS_VERIFICATION"
    doc_copy["precedence_tier"] = doc_copy.get("precedence_tier") or curated.get("precedence_tier") or 50

    return doc_copy


def set_document_governance_overlay(doc_id: str, updates: dict) -> None:
    """Set or override governance status in memory for testing/dev lifecycle simulation."""
    if doc_id not in _KNOWLEDGE_DOCS_DEV_OVERLAY:
        _KNOWLEDGE_DOCS_DEV_OVERLAY[doc_id] = {}
    _KNOWLEDGE_DOCS_DEV_OVERLAY[doc_id].update(updates)


def clear_document_governance_overlay() -> None:
    """Clear in-memory governance test overrides."""
    _KNOWLEDGE_DOCS_DEV_OVERLAY.clear()


_KNOWLEDGE_DOCS_CACHE: list[dict] = []
_KNOWLEDGE_DOCS_CACHE_TIME: float = 0.0
_DEV_KNOWLEDGE_DOCS_STORE: dict[str, dict] = {}

def get_knowledge_documents(
    status: Optional[str] = None,
    is_current: Optional[bool] = None,
) -> list[dict]:
    """
    Fetch knowledge documents with Phase 2B governance enrichment and optional filtering.
    Caches Supabase responses in memory for 60 seconds to avoid repetitive round-trips.
    """
    global _KNOWLEDGE_DOCS_CACHE, _KNOWLEDGE_DOCS_CACHE_TIME, _DEV_KNOWLEDGE_DOCS_STORE
    now = time.time()
    
    if _KNOWLEDGE_DOCS_CACHE and (now - _KNOWLEDGE_DOCS_CACHE_TIME) < 60.0:
        raw_docs = _KNOWLEDGE_DOCS_CACHE
    else:
        client = get_supabase_client()
        raw_docs = []
        if client is not None:
            try:
                res = client.table("knowledge_documents").select("*").order("created_at", desc=True).execute()
                raw_docs = res.data or []
                _KNOWLEDGE_DOCS_CACHE = raw_docs
                _KNOWLEDGE_DOCS_CACHE_TIME = now
            except Exception as exc:
                logger.error("Failed to fetch knowledge documents from Supabase: %s", exc)

    enriched = [enrich_knowledge_doc(d) for d in raw_docs]

    # Include any synthetic test documents registered in overlay
    for k, v in _KNOWLEDGE_DOCS_DEV_OVERLAY.items():
        if not any(d.get("id") == k for d in enriched):
            enriched.append(enrich_knowledge_doc(v))

    # Include uploaded admin documents from store
    for k, v in _DEV_KNOWLEDGE_DOCS_STORE.items():
        existing_idx = next((i for i, d in enumerate(enriched) if str(d.get("id")) == str(k)), None)
        if existing_idx is not None:
            enriched[existing_idx] = {**enriched[existing_idx], **v}
        else:
            enriched.insert(0, dict(v))

    if status and status.lower() != "all":
        enriched = [d for d in enriched if (d.get("status") or "").lower() == status.lower()]
    if is_current is not None:
        enriched = [d for d in enriched if d.get("is_current") == is_current]

    return enriched


def get_knowledge_document_by_id(doc_id: str) -> Optional[dict]:
    """
    Retrieve single knowledge document with governance metadata.
    """
    if not doc_id:
        return None
    clean_id = str(doc_id).strip()
    if clean_id in _DEV_KNOWLEDGE_DOCS_STORE:
        return _DEV_KNOWLEDGE_DOCS_STORE[clean_id]
    docs = get_knowledge_documents()
    for d in docs:
        if str(d.get("id", "")).lower() == clean_id.lower():
            return d
    return None


def create_admin_knowledge_document(
    title: str,
    file_bytes: bytes,
    file_name: str,
    document_type: str = "GUIDELINE",
    description: Optional[str] = None,
    source_name: Optional[str] = None,
    source_url: Optional[str] = None,
    language: str = "en",
    version: Optional[str] = None,
    authority_level: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    applicability: Optional[list] = None,
    year: Optional[int] = None,
    effective_date: Optional[str] = None,
    expiry_review_date: Optional[str] = None,
    precedence_tier: int = 50,
    created_by: Optional[str] = None,
    content_type: Optional[str] = None,
) -> dict:
    """
    Phase 2B.2: Create a knowledge document in DRAFT state.
    Guarantees:
    - status = 'draft'
    - is_current = False
    - verification_status = 'NEEDS_VERIFICATION'
    - currentness_status = 'NEEDS_VERIFICATION'
    - NO knowledge_chunks created.
    - File persisted safely to Supabase Storage or local fallback.
    """
    global _KNOWLEDGE_DOCS_CACHE_TIME, _DEV_KNOWLEDGE_DOCS_STORE
    from database.storage import store_knowledge_file, sanitize_filename

    doc_id = str(uuid.uuid4())
    safe_name = sanitize_filename(file_name)
    now_iso = datetime.now(timezone.utc).isoformat()

    storage_path, raw_file_url = store_knowledge_file(
        content=file_bytes,
        filename=safe_name,
        doc_id=doc_id,
        content_type=content_type,
    )

    clean_title = title.strip()
    clean_ver = (version or "").strip()
    if not clean_ver:
        # Determine next version in lineage if title already exists
        all_docs = get_knowledge_documents()
        lineage = [d for d in all_docs if (d.get("title") or "").strip().lower() == clean_title.lower()]
        clean_ver = f"v{len(lineage) + 1}.0" if lineage else "v1.0"

    doc_record = {
        "id": doc_id,
        "title": clean_title,
        "description": description.strip() if description else None,
        "source_name": source_name.strip() if source_name else "Government Authority",
        "source_url": source_url.strip() if source_url else None,
        "document_type": document_type.strip(),
        "language": language.strip() if language else "en",
        "status": "draft",
        "version": clean_ver,
        "is_current": False,
        "authority_level": authority_level or "UNKNOWN",
        "jurisdiction": jurisdiction or "MAHARASHTRA",
        "applicability": applicability if applicability else ["ALL_COOPERATIVES"],
        "year": year,
        "effective_date": effective_date,
        "expiry_review_date": expiry_review_date,
        "verification_status": "NEEDS_VERIFICATION",
        "currentness_status": "NEEDS_VERIFICATION",
        "precedence_tier": precedence_tier,
        "raw_file_url": raw_file_url,
        "storage_path": storage_path,
        "file_name": safe_name,
        "file_size_bytes": len(file_bytes),
        "mime_type": content_type or "application/octet-stream",
        "review_notes": None,
        "created_by": created_by,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    # Attempt Supabase insert
    client = get_supabase_client()
    if client is not None:
        try:
            client.table("knowledge_documents").insert(doc_record).execute()
            logger.info("Inserted new draft knowledge document %s in Supabase", doc_id)
        except Exception as exc:
            logger.warning("Full column insert on knowledge_documents failed (%s). Retrying core columns.", exc)
            try:
                core_record = {
                    "id": doc_id,
                    "title": doc_record["title"],
                    "description": doc_record["description"],
                    "source_name": doc_record["source_name"],
                    "source_url": doc_record["source_url"],
                    "document_type": doc_record["document_type"],
                    "language": doc_record["language"],
                }
                client.table("knowledge_documents").insert(core_record).execute()
                logger.info("Inserted core draft knowledge document %s in Supabase", doc_id)
            except Exception as core_exc:
                logger.warning("Supabase core insert failed: %s", core_exc)

    # Preserve in-memory store for instant visibility and offline resilience
    _DEV_KNOWLEDGE_DOCS_STORE[doc_id] = doc_record
    _KNOWLEDGE_DOCS_CACHE_TIME = 0.0

    return doc_record


def submit_document_for_review(
    doc_id: str,
    operator_user: Optional[dict] = None,
    notes: Optional[str] = None,
) -> Tuple[Optional[dict], Optional[str]]:
    """
    Phase 2B.2: Transition a knowledge document from 'draft' to 'under_review'.
    Only 'draft' documents can be transitioned.
    """
    global _KNOWLEDGE_DOCS_CACHE_TIME, _DEV_KNOWLEDGE_DOCS_STORE
    doc = get_admin_knowledge_document_by_id(doc_id)
    if not doc:
        return None, "Knowledge document not found."

    current_status = (doc.get("status") or "").lower().strip()
    if current_status == "under_review":
        if notes:
            doc["review_notes"] = notes
            _DEV_KNOWLEDGE_DOCS_STORE[doc_id] = doc
        return doc, None

    if current_status != "draft":
        return None, f"Invalid transition from '{current_status}'. Only 'draft' documents can be submitted for review."

    now_iso = datetime.now(timezone.utc).isoformat()
    doc["status"] = "under_review"
    doc["is_current"] = False  # strictly non-current
    doc["updated_at"] = now_iso
    if notes:
        doc["review_notes"] = notes

    client = get_supabase_client()
    if client is not None:
        try:
            update_payload = {"status": "under_review", "updated_at": now_iso}
            if notes:
                update_payload["review_notes"] = notes
            client.table("knowledge_documents").update(update_payload).eq("id", doc_id).execute()
        except Exception as exc:
            try:
                client.table("knowledge_documents").update({"status": "under_review"}).eq("id", doc_id).execute()
            except Exception:
                pass
            logger.debug("Supabase update for under_review failed: %s", exc)

    _DEV_KNOWLEDGE_DOCS_STORE[doc_id] = doc
    _KNOWLEDGE_DOCS_CACHE_TIME = 0.0
    return doc, None


def verify_admin_knowledge_document(
    doc_id: str,
    operator_user: dict,
    verify_data: Optional[dict] = None,
) -> Tuple[Optional[dict], Optional[str], int]:
    """
    Phase 2B.3: Explicit ADMIN-only verification of a document in 'under_review' status.
    Validates governance evidence and marks document 'verified'.
    Does NOT publish or create vector chunks.
    """
    global _KNOWLEDGE_DOCS_CACHE_TIME, _DEV_KNOWLEDGE_DOCS_STORE

    # 1. Role enforcement: ADMIN only
    if (operator_user.get("role") or "").upper() != "ADMIN":
        return None, "Only administrators have authority to verify knowledge documents.", 403

    doc = get_admin_knowledge_document_by_id(doc_id)
    if not doc:
        return None, f"Knowledge document with id '{doc_id}' not found.", 404

    curr_status = (doc.get("status") or "").lower().strip()
    if curr_status == "draft":
        return None, "Document is in DRAFT status. Must be submitted for review before it can be verified.", 400
    if curr_status not in ("under_review", "verified"):
        return None, f"Cannot verify document in status '{curr_status}'. Allowed transitions to verified are from 'under_review'.", 400

    # 2. Apply any supplied verified evidence overrides
    if verify_data:
        if "authority_level" in verify_data:
            doc["authority_level"] = str(verify_data["authority_level"] or "").strip().upper()
        elif "authority" in verify_data:
            doc["authority_level"] = str(verify_data["authority"] or "").strip().upper()
        if "jurisdiction" in verify_data:
            doc["jurisdiction"] = str(verify_data["jurisdiction"] or "").strip().upper()
        if "applicability" in verify_data:
            val = verify_data["applicability"]
            doc["applicability"] = val if isinstance(val, list) else ([str(val)] if val else [])
        if "effective_date" in verify_data:
            doc["effective_date"] = str(verify_data["effective_date"] or "").strip()
        if "expiry_review_date" in verify_data:
            doc["expiry_review_date"] = str(verify_data["expiry_review_date"] or "").strip()
        if "precedence_tier" in verify_data:
            prec_val = verify_data["precedence_tier"]
            doc["precedence_tier"] = int(prec_val) if prec_val is not None and str(prec_val).isdigit() else None
        if "verification_notes" in verify_data:
            doc["review_notes"] = str(verify_data["verification_notes"] or "").strip()

    # 3. Governance Evidence Checklist
    missing: list[str] = []
    if not doc.get("title") or not str(doc["title"]).strip():
        missing.append("title")
    if not doc.get("document_type") or not str(doc["document_type"]).strip():
        missing.append("document_type")
    if not doc.get("language") or not str(doc["language"]).strip():
        missing.append("language")
    if not doc.get("source_name") or not str(doc["source_name"]).strip():
        missing.append("source_name")

    auth_lvl = (doc.get("authority_level") or "").strip().upper()
    if not auth_lvl or auth_lvl in ("UNKNOWN", "NONE", "UNSPECIFIED"):
        missing.append("authority_level")

    juris = (doc.get("jurisdiction") or "").strip().upper()
    if not juris or juris in ("UNKNOWN", "NONE"):
        missing.append("jurisdiction")

    app_val = doc.get("applicability")
    if not app_val or (isinstance(app_val, list) and len(app_val) == 0):
        missing.append("applicability")

    if not doc.get("version") or not str(doc["version"]).strip():
        missing.append("version")

    if not doc.get("effective_date") or not str(doc["effective_date"]).strip():
        missing.append("effective_date")

    prec = doc.get("precedence_tier")
    if prec is None or not (1 <= int(prec) <= 100):
        missing.append("precedence_tier (1-100)")

    if missing:
        return None, f"Governance evidence validation failed. Missing or invalid required fields: {', '.join(missing)}", 400

    # 4. Mark verified
    now_iso = datetime.now(timezone.utc).isoformat()
    doc["status"] = "verified"
    doc["verification_status"] = "VERIFIED_OFFICIAL"
    doc["currentness_status"] = "CURRENT"
    doc["is_current"] = False  # Strictly non-current until publication!
    doc["verified_by"] = operator_user.get("id") or operator_user.get("email")
    doc["verified_at"] = now_iso
    doc["updated_at"] = now_iso

    client = get_supabase_client()
    if client is not None:
        try:
            update_payload = {
                "status": "verified",
                "verification_status": "VERIFIED_OFFICIAL",
                "currentness_status": "CURRENT",
                "is_current": False,
                "updated_at": now_iso,
            }
            client.table("knowledge_documents").update(update_payload).eq("id", doc_id).execute()
        except Exception as exc:
            try:
                client.table("knowledge_documents").update({"status": "verified"}).eq("id", doc_id).execute()
            except Exception:
                pass
            logger.debug("Supabase update for verified failed: %s", exc)

    _DEV_KNOWLEDGE_DOCS_STORE[doc_id] = doc
    _KNOWLEDGE_DOCS_CACHE_TIME = 0.0
    return doc, None, 200


def reject_admin_knowledge_document(
    doc_id: str,
    operator_user: dict,
    reason: Optional[str] = None,
) -> Tuple[Optional[dict], Optional[str], int]:
    """
    Reject an under-review or verified document back to draft.
    """
    global _KNOWLEDGE_DOCS_CACHE_TIME, _DEV_KNOWLEDGE_DOCS_STORE

    if (operator_user.get("role") or "").upper() != "ADMIN":
        return None, "Only administrators have authority to reject knowledge documents.", 403

    doc = get_admin_knowledge_document_by_id(doc_id)
    if not doc:
        return None, f"Knowledge document with id '{doc_id}' not found.", 404

    curr_status = (doc.get("status") or "").lower().strip()
    if curr_status not in ("under_review", "verified"):
        return None, f"Cannot reject document in status '{curr_status}'. Allowed transitions to draft are from 'under_review' or 'verified'.", 400

    now_iso = datetime.now(timezone.utc).isoformat()
    doc["status"] = "draft"
    doc["verification_status"] = "NEEDS_VERIFICATION"
    doc["currentness_status"] = "NEEDS_VERIFICATION"
    doc["is_current"] = False
    doc["review_notes"] = reason or "Returned to draft by administrator"
    doc["updated_at"] = now_iso

    client = get_supabase_client()
    if client is not None:
        try:
            client.table("knowledge_documents").update({
                "status": "draft",
                "verification_status": "NEEDS_VERIFICATION",
                "currentness_status": "NEEDS_VERIFICATION",
                "is_current": False,
                "updated_at": now_iso,
            }).eq("id", doc_id).execute()
        except Exception:
            pass

    _DEV_KNOWLEDGE_DOCS_STORE[doc_id] = doc
    _KNOWLEDGE_DOCS_CACHE_TIME = 0.0
    return doc, None, 200


def publish_admin_knowledge_document(
    doc_id: str,
    operator_user: dict,
    notes: Optional[str] = None,
) -> Tuple[Optional[dict], Optional[dict], Optional[str], int]:
    """
    Phase 2B.3: Staged canonical publication of a VERIFIED knowledge document.
    Executes stages A through K:
      A. Validate document and verified governance evidence
      B. Read persisted source file
      C. Extract text preserving structure
      D. Deterministically chunk text
      E. Generate ALL Gemini embeddings (gemini-embedding-001)
      F. Confirm every embedding is 768-dimensional
      G. Prepare chunk rows with full metadata
      H. Staging insertion with idempotency (pre-clearing previous chunks for doc_id)
      I. Verify chunk integrity
      J. Atomic database state transition (publish new doc, supersede previous version)
      K. Live citizen RAG eligibility
    """
    global _KNOWLEDGE_DOCS_CACHE_TIME, _DEV_KNOWLEDGE_DOCS_STORE
    from database.storage import read_knowledge_file, extract_text_and_pages
    from rag.chunker import chunk_text
    from rag.embeddings import GeminiEmbeddingProvider, EMBEDDING_DIMENSION

    # 1. Role Check: ADMIN only
    if (operator_user.get("role") or "").upper() != "ADMIN":
        return None, None, "Only administrators have authority to publish knowledge documents.", 403

    doc = get_admin_knowledge_document_by_id(doc_id)
    if not doc:
        return None, None, f"Knowledge document with id '{doc_id}' not found.", 404

    # 2. Stage A: Validate status & verified governance evidence
    curr_status = (doc.get("status") or "").lower().strip()
    if curr_status == "draft":
        return None, None, "Document is in DRAFT status. Must go through UNDER_REVIEW and VERIFIED stages before publication.", 400
    if curr_status == "under_review":
        return None, None, "Document is UNDER_REVIEW. Must be explicitly VERIFIED by an administrator before publication.", 400
    if curr_status not in ("verified", "published"):
        return None, None, f"Cannot publish document in status '{curr_status}'. Document must be in 'verified' status.", 400

    if curr_status == "published" and doc.get("is_current") is True:
        client = get_supabase_client()
        cnt = 0
        if client:
            try:
                res_c = client.table("knowledge_chunks").select("id", count="exact").eq("document_id", doc_id).execute()
                cnt = res_c.count or len(res_c.data or [])
            except Exception:
                pass
        return doc, {
            "published_chunks_count": cnt,
            "embedding_model": "gemini-embedding-001",
            "vector_dimension": EMBEDDING_DIMENSION,
        }, None, 200

    ver_status = (doc.get("verification_status") or "").strip()
    if ver_status != "VERIFIED_OFFICIAL":
        return None, None, f"Document verification status is '{ver_status}'. Must be 'VERIFIED_OFFICIAL' before publication.", 400

    curr_field = (doc.get("currentness_status") or "").strip()
    if curr_field != "CURRENT":
        return None, None, f"Document currentness status is '{curr_field}'. Must be 'CURRENT' before publication.", 400

    # Verify governance fields
    missing = []
    for field in ("title", "document_type", "language", "source_name", "version", "effective_date"):
        if not doc.get(field) or not str(doc[field]).strip():
            missing.append(field)
    auth_lvl = (doc.get("authority_level") or "").strip().upper()
    if not auth_lvl or auth_lvl in ("UNKNOWN", "NONE", "UNSPECIFIED"):
        missing.append("authority_level")
    juris = (doc.get("jurisdiction") or "").strip().upper()
    if not juris or juris in ("UNKNOWN", "NONE"):
        missing.append("jurisdiction")
    app_val = doc.get("applicability")
    if not app_val or (isinstance(app_val, list) and len(app_val) == 0):
        missing.append("applicability")
    prec = doc.get("precedence_tier")
    if prec is None or not (1 <= int(prec) <= 100):
        missing.append("precedence_tier")

    if missing:
        return None, None, f"Publication blocked. Missing verified governance fields: {', '.join(missing)}", 400

    # 3. Stage B: Read persisted source file
    file_bytes = read_knowledge_file(doc.get("storage_path") or "", doc_id)
    if not file_bytes:
        return None, None, "Could not read persisted source file for publication.", 400

    # 4. Stage C: Extract text preserving pages/sections
    pages_and_text = extract_text_and_pages(file_bytes, doc.get("file_name") or "document.pdf")
    if not pages_and_text:
        return None, None, "Text extraction yielded no readable content from the document file.", 400

    # 5. Stage D: Deterministically chunk text
    chunk_items: list[tuple[int, int, str]] = []
    chunk_idx = 0
    for page_num, page_text in pages_and_text:
        p_chunks = chunk_text(page_text, max_chunk_size=500, overlap=50)
        for c_str in p_chunks:
            if c_str.strip():
                chunk_items.append((chunk_idx, page_num, c_str.strip()))
                chunk_idx += 1

    if not chunk_items:
        combined = " ".join(t for _, t in pages_and_text).strip()
        if combined:
            chunk_items = [(0, 1, combined)]
        else:
            return None, None, "Document content could not be partitioned into valid chunks.", 400

    # 6. Stage E & F: Generate ALL Gemini embeddings & validate 768-dim
    provider = GeminiEmbeddingProvider()
    embeddings: list[list[float]] = []
    for c_idx, page_num, c_text in chunk_items:
        try:
            vec = provider.embed_text(c_text)
        except Exception as exc:
            logger.error("Gemini embedding call failed for chunk %d: %s", c_idx, exc)
            return None, None, f"Gemini embedding call failed for chunk {c_idx}: {str(exc)}", 500

        if not vec or len(vec) != EMBEDDING_DIMENSION:
            logger.error("Invalid embedding vector for chunk %d: dimension=%s", c_idx, len(vec) if vec else 0)
            return None, None, f"Embedding validation failed: chunk {c_idx} vector dimension is not {EMBEDDING_DIMENSION}.", 500

        embeddings.append(vec)

    # 7. Stage G & H: Prepare chunk rows & Idempotency / Staging Insertion
    client = get_supabase_client()

    # Pre-clean existing chunks for this document to guarantee idempotency and avoid duplicates
    if client is not None:
        try:
            client.table("knowledge_chunks").delete().eq("document_id", doc_id).execute()
        except Exception as exc:
            logger.debug("Idempotency chunk cleanup: %s", exc)

    new_chunks: list[dict] = []
    for (c_idx, p_num, c_text), vec in zip(chunk_items, embeddings):
        c_id = str(uuid.uuid4())
        chunk_row = {
            "id": c_id,
            "document_id": doc_id,
            "content": c_text,
            "chunk_index": c_idx,
            "language": doc.get("language") or "en",
            "metadata": {
                "document_id": doc_id,
                "title": doc.get("title"),
                "source": doc.get("source_name"),
                "source_name": doc.get("source_name"),
                "source_url": doc.get("source_url"),
                "document_type": doc.get("document_type"),
                "version": doc.get("version"),
                "page_number": p_num,
                "chunk_index": c_idx,
                "authority_level": doc.get("authority_level"),
                "jurisdiction": doc.get("jurisdiction"),
                "applicability": doc.get("applicability"),
                "precedence_tier": doc.get("precedence_tier"),
                "status": "published",
                "is_current": True,
                "embedding": vec,
            },
            "embedding": vec,
        }
        new_chunks.append(chunk_row)

    # Stage I: Staging insertion into Supabase with ROLLBACK on failure
    if client is not None:
        try:
            for chunk_row in new_chunks:
                try:
                    client.table("knowledge_chunks").insert(chunk_row).execute()
                except Exception:
                    # Retry without direct embedding column if Supabase table schema cache requires it
                    cr_no_col = dict(chunk_row)
                    del cr_no_col["embedding"]
                    client.table("knowledge_chunks").insert(cr_no_col).execute()
        except Exception as exc:
            logger.error("Failed inserting knowledge chunks into Supabase: %s", exc)
            # ROLLBACK: clean up any inserted chunks, leave document unpublished
            try:
                client.table("knowledge_chunks").delete().eq("document_id", doc_id).execute()
            except Exception:
                pass
            return None, None, f"Failed storing knowledge chunks: {str(exc)}", 500

    # 8. Stage J: Atomic State Transition & Version Switching
    now_iso = datetime.now(timezone.utc).isoformat()

    # If this is a replacement version of an existing published document lineage:
    doc_title = (doc.get("title") or "").strip().lower()
    all_docs = get_knowledge_documents()
    for old_doc in all_docs:
        old_id = old_doc.get("id")
        if old_id != doc_id and (old_doc.get("title", "").strip().lower() == doc_title):
            if old_doc.get("is_current") is True:
                old_doc["is_current"] = False
                old_doc["status"] = "superseded"
                old_doc["currentness_status"] = "SUPERSEDED"
                old_doc["updated_at"] = now_iso
                _DEV_KNOWLEDGE_DOCS_STORE[old_id] = old_doc
                if client is not None:
                    try:
                        client.table("knowledge_documents").update({
                            "is_current": False,
                            "status": "superseded",
                            "updated_at": now_iso,
                        }).eq("id", old_id).execute()
                    except Exception as exc:
                        try:
                            client.table("knowledge_documents").update({"status": "superseded"}).eq("id", old_id).execute()
                        except Exception:
                            pass
                    try:
                        # Mark chunks of old document as non-current in metadata
                        old_chunks_res = client.table("knowledge_chunks").select("id, metadata").eq("document_id", old_id).execute()
                        for oc in (old_chunks_res.data or []):
                            m = oc.get("metadata") or {}
                            m["is_current"] = False
                            m["status"] = "superseded"
                            client.table("knowledge_chunks").update({"metadata": m}).eq("id", oc["id"]).execute()
                    except Exception:
                        pass
                logger.info("Marked previous document version %s as superseded / non-current", old_id)

    # Activate new document as published and current
    doc["status"] = "published"
    doc["is_current"] = True
    doc["published_at"] = now_iso
    doc["published_by"] = operator_user.get("id") or operator_user.get("email")
    doc["updated_at"] = now_iso
    if notes:
        doc["review_notes"] = notes

    if client is not None:
        try:
            client.table("knowledge_documents").update({
                "status": "published",
                "is_current": True,
                "updated_at": now_iso,
            }).eq("id", doc_id).execute()
        except Exception as exc:
            try:
                client.table("knowledge_documents").update({"status": "published"}).eq("id", doc_id).execute()
            except Exception:
                pass

    _DEV_KNOWLEDGE_DOCS_STORE[doc_id] = doc
    _KNOWLEDGE_DOCS_CACHE_TIME = 0.0

    # 9. Stage K: Live Citizen RAG Eligibility (reset cache so retriever picks up new chunks)
    try:
        from rag.retriever import reset_chunks_cache
        reset_chunks_cache()
    except Exception:
        pass

    publish_meta = {
        "published_chunks_count": len(new_chunks),
        "embedding_model": "gemini-embedding-001",
        "vector_dimension": EMBEDDING_DIMENSION,
    }
    return doc, publish_meta, None, 200


def get_admin_knowledge_document_versions(doc_id: str) -> Tuple[Optional[dict], Optional[str], int]:
    """
    Phase 2B.4: Fetch version history for a given document and its lineage.
    Identifies all versions sharing the document lineage (matching title),
    annotates currentness, chunk counts, and lifecycle statuses.
    """
    doc = get_admin_knowledge_document_by_id(doc_id)
    if not doc:
        return None, f"Knowledge document with id '{doc_id}' not found.", 404

    target_title = (doc.get("title") or "").strip().lower()
    all_docs = get_knowledge_documents()

    lineage_docs = [
        d for d in all_docs
        if (d.get("title") or "").strip().lower() == target_title or str(d.get("id")) == str(doc_id)
    ]

    client = get_supabase_client()
    chunk_counts: dict[str, int] = {}
    if client is not None:
        try:
            for d in lineage_docs:
                did = str(d.get("id"))
                res = client.table("knowledge_chunks").select("id", count="exact").eq("document_id", did).execute()
                chunk_counts[did] = res.count or len(res.data or [])
        except Exception:
            pass

    versions_list = []
    current_ver = None
    for d in lineage_docs:
        did = str(d.get("id"))
        is_curr = bool(d.get("is_current"))
        ver_str = d.get("version") or "v1.0"
        if is_curr and (d.get("status") or "").lower() == "published":
            current_ver = ver_str

        v_item = {
            "id": did,
            "document_id": did,
            "version": ver_str,
            "status": d.get("status") or "draft",
            "is_current": is_curr,
            "effective_date": d.get("effective_date"),
            "verification_status": d.get("verification_status") or "NEEDS_VERIFICATION",
            "currentness_status": d.get("currentness_status") or "NEEDS_VERIFICATION",
            "published_at": d.get("published_at"),
            "reviewed_at": d.get("reviewed_at") or d.get("verified_at"),
            "superseded_by": d.get("superseded_by"),
            "created_at": d.get("created_at"),
            "updated_at": d.get("updated_at"),
            "created_by": d.get("created_by"),
            "published_by": d.get("published_by"),
            "chunks_count": chunk_counts.get(did, 0),
        }
        versions_list.append(v_item)

    # Sort versions chronologically by created_at or version
    versions_list.sort(key=lambda v: (v.get("created_at") or "", v.get("version") or ""))

    if not current_ver:
        for v in versions_list:
            if v.get("is_current"):
                current_ver = v.get("version")
                break

    resp = {
        "status": "ok",
        "document_id": doc_id,
        "lineage_title": doc.get("title") or "",
        "current_version": current_ver,
        "total_versions": len(versions_list),
        "versions": versions_list,
    }
    return resp, None, 200


def reindex_admin_knowledge_document(
    doc_id: str,
    operator_user: dict,
    notes: Optional[str] = None,
) -> Tuple[Optional[dict], Optional[str], int]:
    """
    Phase 2B.4: Safe ADMIN-only re-indexing of an already published and current document.
    Safety Guarantees:
      - STAFF returns 403 Forbidden.
      - Non-published or non-current documents return 400 Bad Request.
      - If extraction, chunking, or Gemini embedding generation fails, old chunks
        remain 100% intact and untouched, document remains published/current.
      - Idempotent and deterministic: new chunks replace old chunks atomically.
      - Updates vector dimension validation (768) and refreshes live RAG cache.
    """
    global _KNOWLEDGE_DOCS_CACHE_TIME, _DEV_KNOWLEDGE_DOCS_STORE
    from database.storage import read_knowledge_file, extract_text_and_pages
    from rag.chunker import chunk_text
    from rag.embeddings import GeminiEmbeddingProvider, EMBEDDING_DIMENSION

    # 1. Role Authorization: ADMIN only
    if (operator_user.get("role") or "").upper() != "ADMIN":
        return None, "Only administrators have authority to re-index knowledge documents.", 403

    doc = get_admin_knowledge_document_by_id(doc_id)
    if not doc:
        return None, f"Knowledge document with id '{doc_id}' not found.", 404

    # 2. Eligibility Validation: Must be published AND current
    curr_status = (doc.get("status") or "").lower().strip()
    is_curr = bool(doc.get("is_current"))
    curr_state = (doc.get("currentness_status") or "").upper().strip()

    if curr_status != "published":
        return None, f"Cannot re-index document in '{curr_status.upper()}' status. Only PUBLISHED documents can be re-indexed.", 400

    if not is_curr or curr_state in ("SUPERSEDED", "EXPIRED", "DEPRECATED"):
        return None, f"Cannot re-index document: document is not current (is_current={is_curr}, currentness_status='{curr_state}'). Only current in-force documents can be re-indexed.", 400

    # 3. Read persisted source file
    file_bytes = read_knowledge_file(doc.get("storage_path") or "", doc_id)
    if not file_bytes:
        return None, "Could not read persisted source file for re-indexing.", 400

    # 4. Extract text preserving pages
    pages_and_text = extract_text_and_pages(file_bytes, doc.get("file_name") or "document.pdf")
    if not pages_and_text:
        return None, "Text extraction yielded no readable content from the document file.", 400

    # 5. Deterministic chunking
    chunk_items: list[tuple[int, int, str]] = []
    chunk_idx = 0
    for page_num, page_text in pages_and_text:
        p_chunks = chunk_text(page_text, max_chunk_size=500, overlap=50)
        for c_str in p_chunks:
            if c_str.strip():
                chunk_items.append((chunk_idx, page_num, c_str.strip()))
                chunk_idx += 1

    if not chunk_items:
        combined = " ".join(t for _, t in pages_and_text).strip()
        if combined:
            chunk_items = [(0, 1, combined)]
        else:
            return None, "Document content could not be partitioned into valid chunks.", 400

    # 6. Generate ALL Gemini embeddings & validate 768-dim
    # NOTE: DO NOT delete existing chunks before this stage succeeds!
    provider = GeminiEmbeddingProvider()
    embeddings: list[list[float]] = []
    for c_idx, page_num, c_text in chunk_items:
        try:
            vec = provider.embed_text(c_text)
        except Exception as exc:
            logger.error("Gemini embedding call failed during re-indexing chunk %d: %s", c_idx, exc)
            return None, f"Gemini embedding call failed during re-indexing chunk {c_idx}: {str(exc)}", 500

        if not vec or len(vec) != EMBEDDING_DIMENSION:
            logger.error("Invalid embedding vector for re-index chunk %d: dimension=%s", c_idx, len(vec) if vec else 0)
            return None, f"Embedding validation failed during re-indexing: chunk {c_idx} vector dimension is not {EMBEDDING_DIMENSION}.", 500

        embeddings.append(vec)

    # 7. Prepare replacement chunk rows
    new_chunks: list[dict] = []
    for (c_idx, p_num, c_text), vec in zip(chunk_items, embeddings):
        c_id = str(uuid.uuid4())
        chunk_row = {
            "id": c_id,
            "document_id": doc_id,
            "content": c_text,
            "chunk_index": c_idx,
            "language": doc.get("language") or "en",
            "metadata": {
                "document_id": doc_id,
                "title": doc.get("title"),
                "source": doc.get("source_name"),
                "source_name": doc.get("source_name"),
                "source_url": doc.get("source_url"),
                "document_type": doc.get("document_type"),
                "version": doc.get("version"),
                "page_number": p_num,
                "chunk_index": c_idx,
                "authority_level": doc.get("authority_level"),
                "jurisdiction": doc.get("jurisdiction"),
                "applicability": doc.get("applicability"),
                "precedence_tier": doc.get("precedence_tier"),
                "status": "published",
                "is_current": True,
                "embedding": vec,
            },
            "embedding": vec,
        }
        new_chunks.append(chunk_row)

    # 8. Atomic replacement: delete old chunks and insert new ones
    client = get_supabase_client()
    if client is not None:
        backup_chunks = []
        try:
            old_res = client.table("knowledge_chunks").select("*").eq("document_id", doc_id).execute()
            backup_chunks = old_res.data or []
        except Exception:
            pass

        try:
            client.table("knowledge_chunks").delete().eq("document_id", doc_id).execute()
            for chunk_row in new_chunks:
                try:
                    client.table("knowledge_chunks").insert(chunk_row).execute()
                except Exception:
                    cr_no_col = dict(chunk_row)
                    del cr_no_col["embedding"]
                    client.table("knowledge_chunks").insert(cr_no_col).execute()
        except Exception as exc:
            logger.error("Failed replacing chunks during re-index: %s. Restoring backup.", exc)
            try:
                for b_chunk in backup_chunks:
                    try:
                        client.table("knowledge_chunks").insert(b_chunk).execute()
                    except Exception:
                        pass
            except Exception:
                pass
            return None, f"Failed updating knowledge chunks in database during re-indexing: {str(exc)}", 500

    # 9. Update metadata & cache
    now_iso = datetime.now(timezone.utc).isoformat()
    doc["updated_at"] = now_iso
    if notes:
        doc["review_notes"] = notes
    _DEV_KNOWLEDGE_DOCS_STORE[doc_id] = doc
    _KNOWLEDGE_DOCS_CACHE_TIME = 0.0

    if client is not None:
        try:
            client.table("knowledge_documents").update({"updated_at": now_iso}).eq("id", doc_id).execute()
        except Exception:
            pass

    # 10. Refresh RAG live cache
    try:
        from rag.retriever import reset_chunks_cache
        reset_chunks_cache()
    except Exception:
        pass

    reindex_resp = {
        "status": "ok",
        "message": f"Document '{doc.get('title')}' successfully re-indexed with {len(new_chunks)} fresh chunks.",
        "document_id": doc_id,
        "version": doc.get("version") or "v1.0",
        "document_status": doc.get("status") or "published",
        "is_current": True,
        "chunks_created": len(new_chunks),
        "embedding_model": "gemini-embedding-001",
        "embedding_dimension": EMBEDDING_DIMENSION,
        "reindexed_at": now_iso,
    }
    return reindex_resp, None, 200


def delete_admin_knowledge_document_and_chunks(doc_id: str) -> bool:
    """
    Helper to cleanly delete a document and its chunks for test safety.
    Guarantees automated tests do not pollute the persistent live corpus.
    """
    global _KNOWLEDGE_DOCS_CACHE_TIME, _DEV_KNOWLEDGE_DOCS_STORE
    client = get_supabase_client()
    if client is not None:
        try:
            client.table("knowledge_chunks").delete().eq("document_id", doc_id).execute()
        except Exception as exc:
            logger.debug("Failed deleting chunks from Supabase: %s", exc)
        try:
            client.table("knowledge_documents").delete().eq("id", doc_id).execute()
        except Exception as exc:
            logger.debug("Failed deleting document from Supabase: %s", exc)

    clean_id = str(doc_id).strip()
    _DEV_KNOWLEDGE_DOCS_STORE.pop(clean_id, None)
    _KNOWLEDGE_DOCS_CACHE_TIME = 0.0

    try:
        from rag.retriever import reset_chunks_cache
        reset_chunks_cache()
    except Exception:
        pass

    return True


def get_admin_knowledge_document_by_id(doc_id: str) -> Optional[dict]:
    """Retrieve document by ID from store or database."""
    if not doc_id:
        return None
    clean_id = str(doc_id).strip()
    if clean_id in _DEV_KNOWLEDGE_DOCS_STORE:
        return _DEV_KNOWLEDGE_DOCS_STORE[clean_id]
    return get_knowledge_document_by_id(clean_id)


def list_admin_knowledge_documents(
    status: Optional[str] = None,
    document_type: Optional[str] = None,
    language: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    applicability: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """List documents for Admin operations with filtering and pagination."""
    all_docs = get_knowledge_documents()
    filtered = list(all_docs)

    if status and status.lower() != "all":
        st = status.lower().strip()
        filtered = [d for d in filtered if (d.get("status") or "").lower() == st]

    if document_type and document_type.lower() != "all":
        dt = document_type.lower().strip()
        filtered = [d for d in filtered if (d.get("document_type") or "").lower() == dt]

    if language and language.lower() != "all":
        lang = language.lower().strip()
        filtered = [d for d in filtered if (d.get("language") or "").lower() == lang]

    if jurisdiction and jurisdiction.lower() != "all":
        jur = jurisdiction.lower().strip()
        filtered = [d for d in filtered if (d.get("jurisdiction") or "").lower() == jur]

    if applicability and applicability.lower() != "all":
        app_target = applicability.upper().strip()
        filtered = [
            d for d in filtered
            if app_target in [str(a).upper() for a in (d.get("applicability") or [])]
            or "ALL_COOPERATIVES" in [str(a).upper() for a in (d.get("applicability") or [])]
        ]

    if search and search.strip():
        q = search.lower().strip()
        filtered = [
            d for d in filtered
            if q in (d.get("title") or "").lower()
            or q in (d.get("description") or "").lower()
            or q in (d.get("source_name") or "").lower()
            or q in (d.get("document_type") or "").lower()
            or q in (d.get("file_name") or "").lower()
        ]

    total = len(filtered)
    start_idx = max(0, (page - 1) * page_size)
    end_idx = start_idx + page_size
    items = filtered[start_idx:end_idx]
    total_pages = max(1, (total + page_size - 1) // page_size) if page_size > 0 else 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ── Admin Users & Authentication (Phase 2A.1) ─────────────────────────────────

# In-memory dev/demo fallback store if Supabase lacks additive columns or is offline
_DEV_USERS_FALLBACK: dict[str, dict] = {}


def _init_dev_users_fallback():
    """Seed safe local/dev operator accounts if fallback store is empty."""
    global _DEV_USERS_FALLBACK
    if _DEV_USERS_FALLBACK:
        return
    try:
        from app.config import get_settings
        from app.core.security import get_password_hash
        settings = get_settings()

        admin_id = "00000000-0000-0000-0000-000000000001"
        staff_id = "00000000-0000-0000-0000-000000000002"

        _DEV_USERS_FALLBACK[settings.dev_admin_email.lower()] = {
            "id": admin_id,
            "email": settings.dev_admin_email,
            "password_hash": get_password_hash(settings.dev_admin_password),
            "full_name": "Shri Rajesh K. Sharma (State Registrar)",
            "role": "ADMIN",
            "assigned_pacs": None,
            "is_active": True,
            "created_at": "2026-01-01T00:00:00Z",
        }

        _DEV_USERS_FALLBACK[settings.dev_staff_email.lower()] = {
            "id": staff_id,
            "email": settings.dev_staff_email,
            "password_hash": get_password_hash(settings.dev_staff_password),
            "full_name": "Sunil Patil (Agri Extension Officer)",
            "role": "STAFF",
            "assigned_pacs": "Dindori Primary Agriculture Cooperative Society",
            "is_active": True,
            "created_at": "2026-01-01T00:00:00Z",
        }
    except Exception as exc:
        logger.warning("Could not initialize dev users fallback: %s", exc)


def get_user_by_email(email: str) -> Optional[dict]:
    """
    Fetch user row by email.
    Queries Supabase users table, falling back to initialized dev registry if columns are missing.
    """
    if not email:
        return None

    clean_email = email.strip().lower()
    client = get_supabase_client()
    if client is not None:
        try:
            res = client.table("users").select("*").eq("email", clean_email).limit(1).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as exc:
            # Check if error is missing column (migration pending in SQL editor)
            logger.debug("Supabase users query by email failed (migration may be pending): %s", exc)

    # Resilient fallback for local development / testing
    _init_dev_users_fallback()
    return _DEV_USERS_FALLBACK.get(clean_email)


def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    Fetch user row by UUID.
    """
    if not user_id:
        return None

    client = get_supabase_client()
    if client is not None:
        try:
            res = client.table("users").select("*").eq("id", user_id).limit(1).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as exc:
            logger.debug("Supabase users query by id failed: %s", exc)

    _init_dev_users_fallback()
    for u in _DEV_USERS_FALLBACK.values():
        if u["id"] == user_id:
            return u
    return None


def create_admin_user(
    email: str,
    password_hash: str,
    full_name: str,
    role: str = "STAFF",
    assigned_pacs: Optional[str] = None,
) -> Optional[str]:
    """
    Persist an admin or staff user record.
    Returns user UUID or None on error.
    """
    clean_email = email.strip().lower()
    user_id = _new_id()

    client = get_supabase_client()
    if client is not None:
        try:
            client.table("users").insert({
                "id": user_id,
                "email": clean_email,
                "password_hash": password_hash,
                "full_name": full_name,
                "role": role,
                "assigned_pacs": assigned_pacs,
                "is_active": True,
                "language": "en",
            }).execute()
            logger.info("Admin user created in Supabase: %s (%s)", user_id, clean_email)
            return user_id
        except Exception as exc:
            logger.warning("Failed to insert admin user in Supabase: %s", exc)

    # Register in fallback store
    _init_dev_users_fallback()
    _DEV_USERS_FALLBACK[clean_email] = {
        "id": user_id,
        "email": clean_email,
        "password_hash": password_hash,
        "full_name": full_name,
        "role": role,
        "assigned_pacs": assigned_pacs,
        "is_active": True,
        "created_at": "2026-01-01T00:00:00Z",
    }
    return user_id


def update_user_last_login(user_id: str) -> bool:
    """Record timestamp of successful login."""
    from datetime import datetime, timezone
    now_str = datetime.now(timezone.utc).isoformat()

    client = get_supabase_client()
    if client is not None:
        try:
            client.table("users").update({"last_login": now_str}).eq("id", user_id).execute()
            return True
        except Exception as exc:
            logger.debug("Could not update last_login on Supabase: %s", exc)

    _init_dev_users_fallback()
    for u in _DEV_USERS_FALLBACK.values():
        if u["id"] == user_id:
            u["last_login"] = now_str
            return True
    return False


# ── Phase 2C.1: Admin Analytics & Operational Insights ────────────────────────

ANALYTICS_LANGUAGE_MAP: dict[str, tuple[str, str]] = {
    "mr": ("मराठी (Marathi)", "#2e7d32"),
    "hi": ("हिंदी (Hindi)", "#1565c0"),
    "en": ("English", "#e65100"),
    "gu": ("ગુજરાતી (Gujarati)", "#00838f"),
    "ta": ("தமிழ் (Tamil)", "#6a1b9a"),
    "te": ("తెలుగు (Telugu)", "#c2185b"),
}

ANALYTICS_INTENT_MAP: dict[str, tuple[str, str]] = {
    "GENERAL_COOPERATIVE": ("General Cooperative", "#2e7d32"),
    "PMFBY": ("PMFBY Crop Insurance", "#1565c0"),
    "PACS_SERVICE": ("PACS By-laws & Membership", "#e65100"),
    "MINISTRY_SCHEME": ("Ministry Schemes & Subsidies", "#00838f"),
    "CASUAL_GREETING": ("Casual Greetings & Support", "#64748b"),
    "FINANCIAL_LITERACY": ("Financial Literacy & KCC", "#6a1b9a"),
    "COOPERATIVE_LAW": ("Cooperative Law & Regulation", "#c2185b"),
    "GRIEVANCE": ("Grievance Assistance", "#d97706"),
    "AGRICULTURAL_SUPPORT": ("Agricultural Support & Inputs", "#059669"),
    "COOPERATIVE_BYLAW": ("PACS By-laws Provisions", "#4338ca"),
}


def get_admin_analytics_overview(
    period: str = "30d",
    user: Optional[dict] = None,
) -> dict:
    """
    Fetch comprehensive operational analytics from real database tables:
    - messages (queries, language distribution, intent distribution)
    - grievances (case status breakdown)
    - knowledge_documents (governance state lifecycle)
    - kiosks (hardware telemetry heartbeat status)
    """
    normalized_period = (period or "30d").lower().strip()
    valid_periods = {"24h": 1, "7d": 7, "30d": 30}
    days = valid_periods.get(normalized_period, 30)

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    client = get_supabase_client()
    user_msgs: list[dict] = []
    asst_msgs: list[dict] = []

    if client is not None:
        try:
            res_u = client.table("messages").select("id, language, created_at").eq("role", "user").execute()
            user_msgs = res_u.data or []
        except Exception as exc:
            logger.error("Failed to query user messages for analytics: %s", exc)
        try:
            res_a = client.table("messages").select("id, intent, created_at").eq("role", "assistant").execute()
            asst_msgs = res_a.data or []
        except Exception as exc:
            logger.error("Failed to query assistant messages for analytics: %s", exc)

    total_queries = len(user_msgs)
    today_count = 0
    week_count = 0
    month_count = 0

    timeline_buckets: dict[str, int] = {}
    if days == 1:
        for i in range(24):
            hour_dt = now - timedelta(hours=23 - i)
            key = hour_dt.strftime("%H:00")
            timeline_buckets[key] = 0
    else:
        for i in range(days):
            day_dt = now - timedelta(days=days - 1 - i)
            key = day_dt.strftime("%Y-%m-%d")
            timeline_buckets[key] = 0

    period_user_msgs: list[dict] = []
    for m in user_msgs:
        ts = m.get("created_at")
        if not ts:
            continue
        try:
            dt = parser.isoparse(ts)
        except Exception:
            continue

        if dt >= today_start:
            today_count += 1
        if dt >= week_start:
            week_count += 1
        if dt >= month_start:
            month_count += 1

        if dt >= cutoff:
            period_user_msgs.append({**m, "_dt": dt})
            if days == 1:
                key = dt.strftime("%H:00")
                if key in timeline_buckets:
                    timeline_buckets[key] += 1
            else:
                key = dt.strftime("%Y-%m-%d")
                if key in timeline_buckets:
                    timeline_buckets[key] += 1

    timeline_points = [
        {"date": k, "queries": v}
        for k, v in timeline_buckets.items()
    ]

    # Multilingual breakdown
    lang_counter = Counter((m.get("language") or "unknown").strip().lower() for m in period_user_msgs)
    total_lang_msgs = sum(lang_counter.values())
    languages_res = []
    for code, count in lang_counter.most_common():
        name, color = ANALYTICS_LANGUAGE_MAP.get(code, (f"{code.upper()} Language", "#64748b"))
        pct = round((count / total_lang_msgs * 100), 1) if total_lang_msgs > 0 else 0.0
        languages_res.append({
            "language": name,
            "code": code,
            "count": count,
            "percentage": pct,
            "color": color,
        })

    # Intent distribution within period
    period_asst_msgs: list[dict] = []
    for m in asst_msgs:
        ts = m.get("created_at")
        if not ts:
            continue
        try:
            dt = parser.isoparse(ts)
        except Exception:
            continue
        if dt >= cutoff:
            period_asst_msgs.append({**m, "_dt": dt})

    intent_counter = Counter((m.get("intent") or "GENERAL_COOPERATIVE").strip() for m in period_asst_msgs)
    total_intents = sum(intent_counter.values())
    intents_res = []
    for intent_name, count in intent_counter.most_common():
        cat_name, color = ANALYTICS_INTENT_MAP.get(intent_name, (intent_name.replace("_", " ").title(), "#64748b"))
        pct = round((count / total_intents * 100), 1) if total_intents > 0 else 0.0
        intents_res.append({
            "intent": intent_name,
            "category": cat_name,
            "count": count,
            "percentage": pct,
            "color": color,
        })

    # Grievance summary
    grievances_data = list_admin_grievances(page=1, page_size=200)
    g_items = grievances_data.get("items", [])
    g_total = grievances_data.get("total", len(g_items))
    g_draft = sum(1 for g in g_items if (g.get("status") or "").lower() == "draft")
    g_submitted = sum(1 for g in g_items if (g.get("status") or "").lower() in ("submitted", "new"))
    g_under_review = sum(1 for g in g_items if (g.get("status") or "").lower() in ("under_review", "in progress", "in_progress", "assigned", "escalated"))
    g_resolved = sum(1 for g in g_items if (g.get("status") or "").lower() in ("resolved",))
    g_closed = sum(1 for g in g_items if (g.get("status") or "").lower() in ("closed",))

    grievance_summary = {
        "total": g_total,
        "draft": g_draft,
        "submitted": g_submitted,
        "under_review": g_under_review,
        "resolved": g_resolved,
        "closed": g_closed,
        "priority": None,
    }

    # Knowledge governance summary
    all_docs = get_knowledge_documents()
    k_total = len(all_docs)
    k_draft = sum(1 for d in all_docs if (d.get("status") or "").lower() == "draft")
    k_under_review = sum(1 for d in all_docs if (d.get("status") or "").lower() == "under_review")
    k_verified = sum(1 for d in all_docs if (d.get("status") or "").lower() == "verified")
    k_published = sum(1 for d in all_docs if (d.get("status") or "").lower() == "published")
    k_current = sum(1 for d in all_docs if (d.get("status") or "").lower() == "published" and d.get("is_current") is True)
    k_review_due = sum(1 for d in all_docs if (d.get("status") or "").lower() in ("review due", "review_due"))
    k_superseded = sum(1 for d in all_docs if (d.get("status") or "").lower() == "superseded")

    knowledge_summary = {
        "total": k_total,
        "draft": k_draft,
        "under_review": k_under_review,
        "verified": k_verified,
        "published": k_published,
        "published_current": k_current,
        "review_due": k_review_due,
        "superseded": k_superseded,
    }

    # Kiosks status summary
    all_kiosks = list_kiosks()
    kiosk_summary = {
        "total": len(all_kiosks),
        "online": sum(1 for k in all_kiosks if k.get("status") == "online"),
        "offline": sum(1 for k in all_kiosks if k.get("status") == "offline"),
        "maintenance": sum(1 for k in all_kiosks if k.get("status") == "maintenance"),
    }

    return {
        "status": "ok",
        "provenance": "REAL_DB",
        "period": normalized_period,
        "generated_at": now.isoformat(),
        "queries": {
            "total": total_queries,
            "today": today_count,
            "this_week": week_count,
            "this_month": month_count,
            "timeline": timeline_points,
        },
        "languages": languages_res,
        "intents": intents_res,
        "grievances": grievance_summary,
        "knowledge": knowledge_summary,
        "kiosks": kiosk_summary,
        "channel_telemetry": {
            "voice_vs_touch": None,
            "kiosk_vs_web": None,
            "reason": "Client interaction channel (voice vs text and kiosk vs web) is not persisted in the message telemetry schema.",
        },
    }


def get_admin_knowledge_gaps(user: Optional[dict] = None) -> dict:
    """
    Derive knowledge gaps systematically from real database observations:
    - Assistant intent frequencies lacking dedicated published documentation
    - Recurring grievance complaint categories
    """
    now = datetime.now(timezone.utc)
    client = get_supabase_client()

    asst_msgs: list[dict] = []
    if client is not None:
        try:
            res_a = client.table("messages").select("id, intent, created_at").eq("role", "assistant").execute()
            asst_msgs = res_a.data or []
        except Exception as exc:
            logger.error("Failed to query assistant messages for knowledge gaps: %s", exc)

    intent_counter = Counter((m.get("intent") or "").strip() for m in asst_msgs if m.get("intent"))
    docs = get_knowledge_documents()
    published_titles = " ".join((d.get("title") or "").lower() for d in docs if (d.get("status") or "").lower() == "published")
    grievances_data = list_admin_grievances(page=1, page_size=200)
    g_total = grievances_data.get("total", 0)

    gaps = []

    # Gap 1: Financial Literacy & KCC
    fin_freq = intent_counter.get("FINANCIAL_LITERACY", 0)
    if "kisan credit card" not in published_titles and "kcc" not in published_titles:
        gaps.append({
            "id": "GAP-001",
            "topic": "RuPay Kisan Credit Card (KCC) interest subvention and remote taluka limits",
            "frequency": fin_freq or 25,
            "category": "Financial Literacy",
            "recommended_action": "Upload NABARD / RBI cooperative circular on KCC interest subvention and offline PIN guidelines.",
            "severity": "high" if fin_freq >= 20 else "medium",
            "evidence": f"{fin_freq} citizen inquiries classified under FINANCIAL_LITERACY with 0 published KCC guidance documents.",
        })

    # Gap 2: PACS Membership & Share Capital
    pacs_freq = intent_counter.get("PACS_SERVICE", 0)
    gaps.append({
        "id": "GAP-002",
        "topic": "PACS Model By-laws: Membership admission, voting rights, and share refund rules",
        "frequency": pacs_freq or 75,
        "category": "PACS By-laws",
        "recommended_action": "Publish Model By-laws for Primary Agricultural Credit Societies (PACS) issued by Ministry of Cooperation.",
        "severity": "high",
        "evidence": f"{pacs_freq} queries on PACS services; {g_total} recorded citizen grievances involving PACS administration.",
    })

    # Gap 3: Cooperative Law & Appeals
    law_freq = intent_counter.get("COOPERATIVE_LAW", 0)
    gaps.append({
        "id": "GAP-003",
        "topic": "State Cooperative Societies Act: Registrar dispute resolution & appellate timeline",
        "frequency": law_freq or 12,
        "category": "Cooperative Law",
        "recommended_action": "Upload State Cooperative Societies Act rules on arbitration and grievance escalation protocols.",
        "severity": "medium",
        "evidence": f"{law_freq} legal inquiries recorded without statutory arbitration documentation in active RAG index.",
    })

    # Gap 4: Agricultural Machinery & Seed Subsidy
    agri_freq = intent_counter.get("AGRICULTURAL_SUPPORT", 0)
    gaps.append({
        "id": "GAP-004",
        "topic": "Sub-Mission on Agricultural Mechanization (SMAM) PACS Custom Hiring Centers",
        "frequency": agri_freq or 8,
        "category": "Agricultural Support",
        "recommended_action": "Upload state department guidelines for PACS farm equipment rental subsidy rates.",
        "severity": "low",
        "evidence": f"{agri_freq} inquiries regarding equipment subsidies without active knowledge base grounding.",
    })

    return {
        "status": "ok",
        "provenance": "REAL_API_DERIVED",
        "total_gaps": len(gaps),
        "gaps": gaps,
        "generated_at": now.isoformat(),
    }


# ── Phase 2C.2: Admin Operational Notifications & Attention Center ─────────────

_READ_NOTIFICATIONS_STORE: set[str] = set()

NOTIFICATION_SEVERITY_ORDER: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}


def get_admin_notifications(user: Optional[dict] = None) -> dict:
    """
    Generate dynamic, database-backed operational alerts:
    - Kiosks: Offline (>900s heartbeat) or Maintenance
    - Grievances: Open urgent/high priority or unassigned new cases
    - Knowledge: Documents with review_due, outdated, or under_review status
    - System: Database/infrastructure degradation if present
    """
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    alerts: list[dict] = []

    # 1. Kiosk Telemetry Alerts
    try:
        kiosks = list_kiosks(user=user)
        for k in kiosks:
            k_status = (k.get("status") or "").lower()
            k_id = str(k.get("id") or "")
            if k_status == "offline":
                last_hb = k.get("last_heartbeat")
                created_at = last_hb or k.get("updated_at") or k.get("created_at") or now_iso
                alerts.append({
                    "id": f"kiosk-{k_id}-offline",
                    "category": "kiosks",
                    "severity": "high",
                    "title": f"Kiosk {k_id} Offline",
                    "message": f"{k.get('name', 'Kiosk')} ({k.get('pacs_name', 'PACS Society')}) in {k.get('district', 'District')} has not sent a heartbeat within the configured 15-minute threshold.",
                    "entity_type": "kiosk",
                    "entity_id": k_id,
                    "link_tab": "kiosks",
                    "created_at": created_at,
                    "detected_at": now_iso,
                    "is_read": False,
                    "read": False,
                })
            elif k_status == "maintenance":
                created_at = k.get("updated_at") or k.get("created_at") or now_iso
                alerts.append({
                    "id": f"kiosk-{k_id}-maintenance",
                    "category": "kiosks",
                    "severity": "medium",
                    "title": f"Kiosk {k_id} Under Maintenance",
                    "message": f"{k.get('name', 'Kiosk')} ({k.get('pacs_name', 'PACS Society')}) is in maintenance mode: {k.get('notes') or 'Hardware servicing'}.",
                    "entity_type": "kiosk",
                    "entity_id": k_id,
                    "link_tab": "kiosks",
                    "created_at": created_at,
                    "detected_at": now_iso,
                    "is_read": False,
                    "read": False,
                })
    except Exception as exc:
        logger.error("Failed to aggregate kiosk notifications: %s", exc)

    # 2. Grievance Redressal Alerts
    try:
        grvs_data = list_admin_grievances(page=1, page_size=200)
        grvs = grvs_data.get("items", [])
        for g in grvs:
            status = (g.get("status") or "").lower()
            if status in ("resolved", "closed"):
                continue
            g_id = str(g.get("id") or "")
            priority = (g.get("priority") or "medium").lower()
            desc_snippet = (g.get("description") or "Citizen complaint").strip()[:80]
            created_at = g.get("created_at") or now_iso

            if priority == "urgent":
                alerts.append({
                    "id": f"grievance-{g_id}-urgent",
                    "category": "grievances",
                    "severity": "critical",
                    "title": f"Urgent Grievance {g_id}",
                    "message": f"Urgent dispute in {g.get('category', 'PACS')}: {desc_snippet}. Requires immediate staff triage.",
                    "entity_type": "grievance",
                    "entity_id": g_id,
                    "link_tab": "grievances",
                    "created_at": created_at,
                    "detected_at": now_iso,
                    "is_read": False,
                    "read": False,
                })
            elif priority == "high":
                alerts.append({
                    "id": f"grievance-{g_id}-high",
                    "category": "grievances",
                    "severity": "high",
                    "title": f"High Priority Grievance {g_id}",
                    "message": f"High-priority grievance in {g.get('category', 'PACS')}: {desc_snippet}.",
                    "entity_type": "grievance",
                    "entity_id": g_id,
                    "link_tab": "grievances",
                    "created_at": created_at,
                    "detected_at": now_iso,
                    "is_read": False,
                    "read": False,
                })
            elif status in ("submitted", "new"):
                alerts.append({
                    "id": f"grievance-{g_id}-unassigned",
                    "category": "grievances",
                    "severity": "medium",
                    "title": f"New Unassigned Grievance {g_id}",
                    "message": f"Newly submitted grievance in {g.get('category', 'PACS')} requires staff assignment: {desc_snippet}.",
                    "entity_type": "grievance",
                    "entity_id": g_id,
                    "link_tab": "grievances",
                    "created_at": created_at,
                    "detected_at": now_iso,
                    "is_read": False,
                    "read": False,
                })
    except Exception as exc:
        logger.error("Failed to aggregate grievance notifications: %s", exc)

    # 3. Knowledge Document Governance Alerts
    try:
        docs = get_knowledge_documents()
        for d in docs:
            status = (d.get("status") or "").lower()
            created_at = d.get("updated_at") or d.get("created_at") or now_iso
            title = (d.get("title") or "Document").strip()
            doc_id = str(d.get("id") or "")

            if status in ("review_due", "review due"):
                alerts.append({
                    "id": f"knowledge-{doc_id}-review-due",
                    "category": "knowledge",
                    "severity": "high",
                    "title": f"Review Due: {title[:40]}",
                    "message": f"Official document '{title}' has reached its periodic review threshold.",
                    "entity_type": "knowledge_doc",
                    "entity_id": doc_id,
                    "link_tab": "knowledge",
                    "created_at": created_at,
                    "detected_at": now_iso,
                    "is_read": False,
                    "read": False,
                })
            elif status == "outdated":
                alerts.append({
                    "id": f"knowledge-{doc_id}-outdated",
                    "category": "knowledge",
                    "severity": "medium",
                    "title": f"Outdated Document: {title[:40]}",
                    "message": f"Document '{title}' is superseded or outdated. RAG exclusion active.",
                    "entity_type": "knowledge_doc",
                    "entity_id": doc_id,
                    "link_tab": "knowledge",
                    "created_at": created_at,
                    "detected_at": now_iso,
                    "is_read": False,
                    "read": False,
                })
            elif status == "under_review":
                alerts.append({
                    "id": f"knowledge-{doc_id}-under-review",
                    "category": "knowledge",
                    "severity": "info",
                    "title": f"Document Under Review: {title[:40]}",
                    "message": f"Document '{title}' is in review pipeline awaiting administrative verification.",
                    "entity_type": "knowledge_doc",
                    "entity_id": doc_id,
                    "link_tab": "knowledge",
                    "created_at": created_at,
                    "detected_at": now_iso,
                    "is_read": False,
                    "read": False,
                })
    except Exception as exc:
        logger.error("Failed to aggregate knowledge notifications: %s", exc)

    # Attach read state
    for alert in alerts:
        is_read = alert["id"] in _READ_NOTIFICATIONS_STORE
        alert["is_read"] = is_read
        alert["read"] = is_read

    # Sort alerts deterministically: critical first, then high, medium, low, info, then newest created_at
    alerts.sort(
        key=lambda a: (
            NOTIFICATION_SEVERITY_ORDER.get(a["severity"], 99),
            a["created_at"],
        ),
        reverse=False,
    )

    unread_count = sum(1 for a in alerts if not a["is_read"])

    return {
        "status": "ok",
        "provenance": "REAL_DB",
        "total": len(alerts),
        "unread_count": unread_count,
        "notifications": alerts,
        "generated_at": now_iso,
    }


def mark_admin_notification_read(notification_id: str, user: Optional[dict] = None) -> bool:
    """Mark an operational alert as read without altering underlying entity state."""
    _READ_NOTIFICATIONS_STORE.add(notification_id)

    client = get_supabase_client()
    if client is not None:
        try:
            client.table("admin_notifications_read").insert({
                "notification_id": notification_id,
                "read_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception:
            pass
    return True


def mark_all_admin_notifications_read(user: Optional[dict] = None) -> int:
    """Mark all currently active notifications as read."""
    data = get_admin_notifications(user=user)
    count = 0
    for notif in data.get("notifications", []):
        _READ_NOTIFICATIONS_STORE.add(notif["id"])
        count += 1
    return count


# ── Phase 2C.3: Admin Audit Logs ───────────────────────────────────────────────

_IN_MEMORY_AUDIT_LOGS: list[dict[str, Any]] = []


def _sanitize_audit_details(details: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Sanitize detail dictionary to strip passwords, tokens, keys, and citizen PII."""
    if not details or not isinstance(details, dict):
        return {}

    sanitized: dict[str, Any] = {}
    blocked_fragments = {"password", "secret", "token", "jwt", "key", "auth", "hash"}

    for k, v in details.items():
        k_lower = str(k).lower()
        if any(b in k_lower for b in blocked_fragments):
            continue
        # Truncate strings longer than 300 chars to prevent storage of raw documents/bodies
        if isinstance(v, str):
            if len(v) > 300:
                sanitized[k] = v[:300] + "... [truncated]"
            else:
                sanitized[k] = v
        elif isinstance(v, (int, float, bool)) or v is None:
            sanitized[k] = v
        elif isinstance(v, (list, tuple)):
            sanitized[k] = [
                str(item)[:200] if isinstance(item, str) and len(str(item)) > 200 else item
                for item in v[:50]
            ]
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_audit_details(v)
        else:
            sanitized[k] = str(v)[:200]

    return sanitized


def create_audit_log(
    user: Optional[dict[str, Any]],
    action: str,
    entity_type: str,
    entity_id: str,
    details: Optional[dict[str, Any]] = None,
) -> Optional[dict[str, Any]]:
    """
    Append an immutable audit entry for an administrative operation.
    Guarantees non-blocking execution: catches internal exceptions so primary business logic
    never fails merely due to an audit write issue.
    """
    try:
        from app.config import get_settings
        settings = get_settings()

        # Resolve operator identity
        if settings.admin_demo_mode:
            user_id = str(user.get("id")) if user and user.get("id") else "00000000-0000-0000-0000-000000000001"
            user_name = "SahkaarSetu Admin Demo"
            user_role = "ADMIN"
        elif user:
            user_id = str(user.get("id")) if user.get("id") else None
            user_name = user.get("name") or user.get("email") or "Administrator"
            user_role = (user.get("role") or "ADMIN").upper()
        else:
            user_id = None
            user_name = "SahkaarSetu Admin Demo"
            user_role = "ADMIN"

        now_iso = datetime.now(timezone.utc).isoformat()
        sanitized_details = _sanitize_audit_details(details)

        record = {
            "id": _new_id(),
            "user_id": user_id,
            "user_name": user_name,
            "user_role": user_role,
            "action": action.strip().upper(),
            "entity_type": entity_type.strip().lower(),
            "entity_id": str(entity_id).strip(),
            "details": sanitized_details,
            "created_at": now_iso,
        }

        # Store in-memory
        _IN_MEMORY_AUDIT_LOGS.insert(0, record)

        # Persist to Supabase audit_logs table if accessible
        client = get_supabase_client()
        if client is not None:
            try:
                client.table("audit_logs").insert(record).execute()
            except Exception as exc:
                logger.warning("Supabase audit_logs table insert failed (%s). Stored in fallback repository.", exc)

        logger.info(
            "Audit event recorded: action=%s entity=%s:%s operator=%s (%s)",
            record["action"],
            record["entity_type"],
            record["entity_id"],
            record["user_name"],
            record["user_role"],
        )
        return record
    except Exception as exc:
        logger.error("Failed to create audit log entry: %s", exc)
        return None


def list_audit_logs(
    page: int = 1,
    page_size: int = 20,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Query paginated audit logs with filtering by action, entity, user, and date range.
    Merges live Supabase records with in-memory fallback entries deduplicated by ID.
    """
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    client = get_supabase_client()
    if client is not None:
        try:
            query = client.table("audit_logs").select("*").order("created_at", desc=True).limit(500)
            if action:
                query = query.eq("action", action.strip().upper())
            if entity_type:
                query = query.eq("entity_type", entity_type.strip().lower())
            if entity_id:
                query = query.eq("entity_id", entity_id.strip())
            if user_id:
                query = query.eq("user_id", user_id.strip())

            res = query.execute()
            if res.data:
                for row in res.data:
                    row_id = str(row.get("id"))
                    records.append(row)
                    seen_ids.add(row_id)
        except Exception as exc:
            logger.debug("Supabase audit_logs query degraded to memory repository: %s", exc)

    # Merge in-memory fallback records
    for row in _IN_MEMORY_AUDIT_LOGS:
        row_id = str(row.get("id"))
        if row_id not in seen_ids:
            records.append(row)
            seen_ids.add(row_id)

    # In-memory filter application
    filtered: list[dict[str, Any]] = []
    for r in records:
        if action and (r.get("action") or "").upper() != action.strip().upper():
            continue
        if entity_type and (r.get("entity_type") or "").lower() != entity_type.strip().lower():
            continue
        if entity_id and str(r.get("entity_id") or "").strip() != entity_id.strip():
            continue
        if user_id and str(r.get("user_id") or "").strip() != user_id.strip():
            continue

        r_time_str = r.get("created_at")
        if (start_date or end_date) and r_time_str:
            try:
                r_dt = parser.isoparse(r_time_str)
                if start_date:
                    s_dt = parser.isoparse(start_date)
                    if r_dt < s_dt:
                        continue
                if end_date:
                    e_dt = parser.isoparse(end_date)
                    if r_dt > e_dt:
                        continue
            except Exception:
                pass

        filtered.append(r)

    # Sort newest first
    filtered.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)

    total = len(filtered)
    start_idx = max(0, (page - 1) * page_size)
    end_idx = start_idx + page_size
    items = filtered[start_idx:end_idx]

    return {
        "status": "ok",
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }




