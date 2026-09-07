"""
Pre-retrieval Knowledge Router for SahkaarSetu (SIH26088).

Routes user query into execution paths BEFORE database retrieval:
1. GREETING: Fast-path direct response (0 RAG, 0 Web Search, 0 LLM).
2. CONVERSATIONAL: Direct LLM response (0 RAG).
3. STABLE_DOMAIN: Vector RAG search first.
4. CURRENT_INFORMATION: Live web search + RAG.
5. COMPLEX_DOMAIN: RAG + web search.
6. UNKNOWN: Web search + LLM (for any general knowledge question).
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import NamedTuple

from app.schemas.query import IntentCode

logger = logging.getLogger(__name__)


class RouterMode(str, Enum):
    GREETING = "GREETING"
    CONVERSATIONAL = "CONVERSATIONAL"
    STABLE_DOMAIN = "STABLE_DOMAIN"
    CURRENT_INFORMATION = "CURRENT_INFORMATION"
    COMPLEX_DOMAIN = "COMPLEX_DOMAIN"
    UNKNOWN = "UNKNOWN"


class RoutingDecision(NamedTuple):
    mode: RouterMode
    trigger_rag: bool
    trigger_web: bool


# Keywords indicating current or time-sensitive queries requiring live web search
CURRENT_INFO_KEYWORDS: set[str] = {
    "current minister", "who is the minister", "latest deadline", "last date",
    "today", "notification", "recent", "latest news", "current officer",
    "tractor", "farm machinery", "equipment", "subsidy", "smam",
    "latest", "right now", "currently", "2024", "2025", "2026",
    "who is", "what is the current", "price today", "rate today",
    "prime minister", "president of india", "chief minister",
    "pradhan mantri", "mukhyamantri",
    "tractor", "farm machinery", "equipment",
    "subsidy", "smam",
    "whos", "who's",
}

# Keywords indicating complex credit / land queries requiring domain RAG search
COMPLEX_KEYWORDS: set[str] = {
    "acre", "acres", "land", "loan", "loans",
    "farming loan", "agricultural loan", "crop loan",
    "how to apply", "application process",
}


def route_query(message: str, intent: IntentCode) -> RoutingDecision:
    """
    Determine the optimal Knowledge Routing decision for a user query.
    All general knowledge questions now trigger web search so Gemini
    can give grounded, up-to-date answers for ANY topic.
    """
    msg_lower = message.lower().strip()

    # Rule 1: Greetings (Fast Path - 0 RAG, 0 Web Search, 0 LLM)
    if intent in {"CASUAL_GREETING", "GREETING"}:
        return RoutingDecision(RouterMode.GREETING, trigger_rag=False, trigger_web=False)

    # Rule 2: Conversational (Thanks, Identity, Unclear)
    if intent in {"CASUAL_THANKS", "CASUAL_IDENTITY", "UNCLEAR"}:
        return RoutingDecision(RouterMode.CONVERSATIONAL, trigger_rag=False, trigger_web=False)

    # Rule 3: Current Information & time-sensitive queries (Live Web Search required)
    if any(kw in msg_lower for kw in CURRENT_INFO_KEYWORDS):
        return RoutingDecision(RouterMode.CURRENT_INFORMATION, trigger_rag=True, trigger_web=True)

    # Rule 4: Complex Domain Queries (Land, Loans) -> RAG search + Web
    if any(kw in msg_lower for kw in COMPLEX_KEYWORDS) or intent == "AGRICULTURAL_SUPPORT":
        return RoutingDecision(RouterMode.COMPLEX_DOMAIN, trigger_rag=True, trigger_web=True)

    # Rule 5: Stable Knowledge Domains (PACS, By-laws, Laws, PMFBY overview)
    if intent in {"PACS_SERVICE", "COOPERATIVE_BYLAW", "COOPERATIVE_LAW", "PMFBY", "MINISTRY_SCHEME", "FINANCIAL_LITERACY", "GRIEVANCE"}:
        return RoutingDecision(RouterMode.STABLE_DOMAIN, trigger_rag=True, trigger_web=False)

    # Rule 6: Default / Unknown Queries -> trigger web search so Gemini can answer
    # anything (general knowledge, science, history, technology, etc.)
    return RoutingDecision(RouterMode.UNKNOWN, trigger_rag=False, trigger_web=True)
