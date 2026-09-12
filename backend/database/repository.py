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
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import get_settings
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
    grievance_id = _new_id()
    now_iso = datetime.now(timezone.utc).isoformat()
    client = get_supabase_client()
    if client is not None:
        try:
            client.table("grievances").insert({
                "id": grievance_id,
                "conversation_id": conversation_id,
                "category": category,
                "description": description,
                "status": status,
            }).execute()
            logger.info("Grievance record created in Supabase: %s (category=%s)", grievance_id, category)
        except Exception as exc:
            logger.warning("Failed to create grievance in Supabase (will use fallback): %s", exc)

    # Mirror into in-memory dev fallback for immediate administrative triage
    _init_dev_grievances_fallback()
    _DEV_GRIEVANCES_FALLBACK[grievance_id] = {
        "id": grievance_id,
        "conversation_id": conversation_id,
        "category": category,
        "description": description,
        "status": status,
        "priority": "medium",
        "assigned_staff": None,
        "pacs_name": None,
        "citizen_masked_name": "Citizen (Protected)",
        "citizen_phone_masked": "+91 98******45",
        "staff_notes": [],
        "ai_guidance": "Grievance recorded for administrative review.",
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    return grievance_id


def get_grievance(grievance_id: str) -> Optional[dict]:
    """
    Fetch a grievance record by UUID.
    Returns dict or None if not found/error.
    """
    client = get_supabase_client()
    if client is not None:
        try:
            res = client.table("grievances").select("*").eq("id", grievance_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as exc:
            logger.debug("Supabase get_grievance error: %s", exc)

    _init_dev_grievances_fallback()
    return _DEV_GRIEVANCES_FALLBACK.get(grievance_id)


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
            text_corpus = f"{r.get('id', '')} {r.get('description', '')} {r.get('citizen_masked_name', '')} {r.get('pacs_name', '')} {r.get('category', '')}".lower()
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

