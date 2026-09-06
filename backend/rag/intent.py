"""
Neutral Intent Classification Router for SahkaarSetu (SIH26088).

Decoupled from AI providers — uses lightweight regex and keyword rules
to route queries to appropriate domain handlers.
"""
from __future__ import annotations

import logging
import re
from app.schemas.query import IntentCode

logger = logging.getLogger(__name__)

# Intent rules evaluated in priority order.
# (Keywords list, Intent Code)
_INTENT_RULES: list[tuple[list[str], IntentCode]] = [
    # Domain specific rules evaluated first
    (
        ["pmfby", "fasal bima", "फसल बीमा", "पीएमएफबीवाय", "पीएमएफबीवाई", "crop insurance",
         "pradhan mantri fasal", "पीक विमा", "पिक विमा", "soyabeen", "soybean", "सोयाबीन",
         "peek kharab", "पिक खराब", "पीक खराब", "paus", "pausa", "pavsa", "पाऊस", "पावसामुळे",
         "crop damage", "crop damaged", "rain damage", "नुकसान", "पिकाचे नुकसान", "पिकाचे"],
        "PMFBY",
    ),
    (
        ["pacs", "पैक्स", "पॅक्स", "primary agricultural credit",
         "प्राथमिक कृषि", "प्राथमिक कृषी", "primary agri"],
        "PACS_SERVICE",
    ),
    (
        ["grievance", "complaint", "शिकायत", "तक्रार", "dispute",
         "redressal", "निवारण"],
        "GRIEVANCE",
    ),
    (
        ["by-law", "bylaw", "उपनियम", "उपविधी", "bye-law",
         "society rules", "नियमावली"],
        "COOPERATIVE_BYLAW",
    ),
    (
        ["cooperative law", "cooperative act", "सहकारी कानून", "सहकारी कायदा",
         "maharashtra cooperative", "mcs act", "section", "registration", "नियम", "नियमांबद्दल", "कायदे"],
        "COOPERATIVE_LAW",
    ),
    (
        ["financial literacy", "वित्तीय साक्षरता", "आर्थिक साक्षरता",
         "kcc", "kisan credit", "किसान क्रेडिट", "saving", "बचत", "investment", "निवेश", "budget", "interest",
         "emi", "fd", "fixed deposit", "credit card"],
        "FINANCIAL_LITERACY",
    ),
    (
        ["scheme", "योजना", "yojana", "subsidy", "अनुदान", "benefit",
         "ministry", "government scheme", "sarkar", "सरकार", "ministry of cooperation", "सहकार मंत्रालय", "सहकारिता मंत्रालय"],
        "MINISTRY_SCHEME",
    ),
    (
        ["crop loan", "agricultural loan", "farming loan", "farm loan", "agricultural support",
         "loan", "loans", "land", "acres", "acre", "कर्ज", "ऋण", "जमीन", "एकर",
         "krishi", "कृषि", "शेती", "fertilizer", "seed", "peek", "पीक", "पिक", "kharab", "नुकसान"],
        "AGRICULTURAL_SUPPORT",
    ),
    # Casual intents evaluated if no domain intent matched
    (
        ["hello", "hi", "hey", "namaskar", "namaste", "नमस्कार", "नमस्ते", "हॅलो", "हेलो", "कसे आहात", "कैसे हो", "good morning", "good evening", "vanakkam", "namaskaram", "kuch to bolo"],
        "CASUAL_GREETING",
    ),
    (
        ["धन्यवाद", "शुक्रिया", "आभार", "thank you", "thanks", "thankyou", "dhanyawad", "dhanyavaad", "aabhar"],
        "CASUAL_THANKS",
    ),
    (
        ["who are you", "what can you do", "तुम्ही कोण आहात", "तुम्ही काय करू शकता", "तुम कौन हो", "आप क्या कर सकते हैं", "sahkaarsetu काय आहे", "sahkaarsetu kya hai"],
        "CASUAL_IDENTITY",
    ),
    (
        ["मला मदत हवी आहे", "मदत हवी आहे", "मदद चाहिए", "मदद करो", "help me", "i need help", "मदत करा"],
        "UNCLEAR",
    ),
]


def classify_intent(message: str) -> IntentCode:
    """
    Classify user message into an IntentCode using rule-based keyword matching.
    Returns domain intent if present, casual greeting if purely casual, or GENERAL_COOPERATIVE as default.
    """
    msg_lower = message.lower().strip()

    for keywords, intent in _INTENT_RULES:
        if any(kw in msg_lower for kw in keywords):
            return intent

    return "GENERAL_COOPERATIVE"


# Backwards compatibility alias
_classify_intent = classify_intent
