"""
Conversational State Manager for SahkaarSetu (SIH26088).

Maintains multi-turn conversation context, pending slot requirements (e.g. STATE, CROP),
collected slots, and prevents repeated questions across user turns.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Standard Indian states dictionary for multi-language slot extraction
STATE_MAP: dict[str, str] = {
    "maharashtra": "Maharashtra",
    "महाराष्ट्र": "Maharashtra",
    "महाराष्ट्र": "Maharashtra",
    "mh": "Maharashtra",
    "hindi": "Hindi",
    "madhya pradesh": "Madhya Pradesh",
    "मध्य प्रदेश": "Madhya Pradesh",
    "मप्र": "Madhya Pradesh",
    "uttar pradesh": "Uttar Pradesh",
    "उत्तर प्रदेश": "Uttar Pradesh",
    "यूपी": "Uttar Pradesh",
    "gujarat": "Gujarat",
    "गुजरात": "Gujarat",
    "punjab": "Punjab",
    "पंजाब": "Punjab",
    "haryana": "Haryana",
    "हरियाणा": "Haryana",
    "karnataka": "Karnataka",
    "कर्नाटक": "Karnataka",
    "rajasthan": "Rajasthan",
    "राजस्थान": "Rajasthan",
    "tamil nadu": "Tamil Nadu",
    "तमिलनाडु": "Tamil Nadu",
    "telangana": "Telangana",
    "तेलंगाना": "Telangana",
    "andhra pradesh": "Andhra Pradesh",
    "आंध्र प्रदेश": "Andhra Pradesh",
    "bihar": "Bihar",
    "बिहार": "Bihar",
    "west bengal": "West Bengal",
    "पश्चिम बंगाल": "West Bengal",
}


@dataclass
class SessionState:
    session_id: str
    turn_number: int = 0
    topic: Optional[str] = None
    user_goal: Optional[str] = None
    pending_slot: Optional[str] = None  # STATE | CROP | COOPERATIVE_TYPE | GRIEVANCE_TYPE
    collected_slots: dict[str, str] = field(default_factory=dict)
    last_assistant_question: Optional[str] = None
    history: list[dict[str, str]] = field(default_factory=list)


# In-memory session store mapping session_id -> SessionState
_SESSIONS: dict[str, SessionState] = {}


def get_or_create_session(session_id: str) -> SessionState:
    """Retrieve existing session state or create a new session instance."""
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = SessionState(session_id=session_id)
    return _SESSIONS[session_id]


def extract_slot_from_message(message: str, pending_slot: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Extract slot value from user message based on pending requirement.
    Returns (slot_name, slot_value).
    """
    if not message or not pending_slot:
        return None, None

    msg_lower = message.lower().strip()

    if pending_slot == "STATE":
        for kw, canonical_state in STATE_MAP.items():
            if kw in msg_lower:
                return "state", canonical_state
        # Generic state pattern match e.g. "I am from Maharashtra"
        match = re.search(r'(?:from|in|state|माहाराष्ट्र|महाराष्ट्रातून|से)\s+([a-zA-Z\u0900-\u097F]+)', message, re.IGNORECASE)
        if match:
            cand = match.group(1).lower()
            if cand in STATE_MAP:
                return "state", STATE_MAP[cand]

    elif pending_slot == "CROP":
        crops = ["soybean", "wheat", "cotton", "rice", "sugarcane", "सोयाबीन", "गहू", "कापूस", "तांदूळ", "ऊस"]
        for c in crops:
            if c in msg_lower:
                return "crop", c

    return None, None


def detect_pending_slot_from_answer(answer_text: str) -> Optional[str]:
    """
    Detect if the assistant's answer asks a new missing question.
    """
    if not answer_text:
        return None

    text_lower = answer_text.lower()
    if any(q in text_lower for q in ["which state", "what state", "कोणत्या राज्यातील", "किस राज्य"]):
        return "STATE"
    if any(q in text_lower for q in ["which crop", "what crop", "कोणते पीक", "कौन सी फसल"]):
        return "CROP"
    if any(q in text_lower for q in ["which society", "pacs member", "कोणत्या संस्थेचे"]):
        return "COOPERATIVE_TYPE"

    return None
