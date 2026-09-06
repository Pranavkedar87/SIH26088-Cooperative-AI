"""
Neutral Intent Classification & Topic Extraction Router for SahkaarSetu (SIH26088).

Decoupled from AI providers — uses lightweight regex and keyword rules
to route queries to appropriate domain handlers and extract user goals.
"""
from __future__ import annotations

import logging
import re
from app.schemas.query import IntentCode

logger = logging.getLogger(__name__)

# Intent rules evaluated in priority order.
_INTENT_RULES: list[tuple[list[str], IntentCode]] = [
    # Domain specific rules evaluated first
    (
        ["pmfby", "fasal bima", "फसल बीमा", "पीएमएफबीवाय", "पीएमएफबीवाई", "crop insurance",
         "pradhan mantri fasal", "पीक विमा", "पिक विमा", "soyabeen", "soybean", "सोयाबीन",
         "peek kharab", "पिक खराब", "पीक खराब", "paus", "pausa", "pavsa", "पाऊस", "पावसामुळे",
         "crop damage", "crop damaged", "rain damage", "heavy rain", "crop get damage",
         "crop suffered damage", "crop loss", "damage because", "damaged because",
         "excessive rain", "unseasonal rain", "नुकसान", "पिकाचे नुकसान", "पिकाचे"],
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
        ["tractor", "machinery", "equipment", "ट्रॅक्टर", "ट्रैक्टर", "smam", "अवजारे", "उपकरण", "tractor subsidy", "ट्रॅक्टर अनुदान", "ट्रैक्टर सब्सिडी"],
        "MINISTRY_SCHEME",
    ),
    (
        ["crop loan", "agricultural loan", "farming loan", "farm loan", "agricultural support",
         "kcc", "land loan", "acres loan", "कर्ज", "ऋण", "कृषि ऋण", "शेती कर्ज",
         "krishi loan", "fertilizer loan", "seed loan"],
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
    """
    msg_lower = message.lower().strip()

    for keywords, intent in _INTENT_RULES:
        if any(kw in msg_lower for kw in keywords):
            return intent

    return "GENERAL_COOPERATIVE"


def extract_topic_and_goal(message: str) -> tuple[str, str]:
    """
    Extract practical topic and user goal from the message.
    Example:
      "I want to buy a tractor any government scheme available for that"
      -> topic="TRACTOR_PURCHASE", user_goal="FINANCIAL_ASSISTANCE_FOR_AGRICULTURAL_MACHINERY"
    """
    msg_lower = message.lower().strip()

    if any(kw in msg_lower for kw in ["tractor", "machinery", "equipment", "ट्रॅक्टर", "ट्रैक्टर", "अवजारे", "उपकरण"]):
        return "TRACTOR_PURCHASE", "FINANCIAL_ASSISTANCE_FOR_AGRICULTURAL_MACHINERY"
    if any(kw in msg_lower for kw in ["crop loan", "agricultural loan", "farm loan", "kcc", "कर्ज", "ऋण"]):
        return "AGRICULTURAL_LOAN", "APPLY_FOR_CROP_LOAN_CREDIT"
    if any(kw in msg_lower for kw in ["pmfby", "crop insurance", "फसल बीमा", "पीक विमा", "पिक विमा"]):
        return "CROP_INSURANCE", "ENROLL_OR_CLAIM_CROP_INSURANCE"
    if any(kw in msg_lower for kw in ["pacs", "पैक्स", "पॅक्स"]):
        return "PACS_MEMBERSHIP", "ACCESS_PACS_COOPERATIVE_SERVICES"

    return "GENERAL_COOPERATIVE_QUERY", "INFORMATION_ASSISTANCE"


def extract_answer_focus(message: str) -> str:
    """
    Extract internal answer focus (PROCEDURE, DOCUMENTS, CONTACT, ELIGIBILITY, DEADLINE, NEXT_STEP, COMPLAINT, OVERVIEW)
    from user message to drive targeted follow-up responses.
    """
    msg_lower = message.lower().strip()

    if any(kw in msg_lower for kw in ["procedure", "process", "step", "steps", "how to", "how do i", "guideline", "guidelines", "प्रक्रिया", "टप्पा", "टप्पे", "कसे करावे", "चरण", "प्रक्रिया क्या"]):
        return "PROCEDURE"
    if any(kw in msg_lower for kw in ["document", "documents", "record", "records", "paper", "papers", "proof", "7/12", "7-12", "8a", "khasra", "khatauni", "passbook", "aadhaar", "कागदपत्रे", "दस्तावेज", "पुरावे"]):
        return "DOCUMENTS"
    if any(kw in msg_lower for kw in ["contact", "helpline", "number", "phone", "email", "office", "officer", "authority", "ddr", "call", "who to contact", "who should i contact", "sampark", "संपर्क", "हेल्पलाईन", "हेल्पलाइन", "अधिकारी"]):
        return "CONTACT"
    if any(kw in msg_lower for kw in ["eligibility", "eligible", "criteria", "who can apply", "qualification", "पात्रता", "अहर्ता"]):
        return "ELIGIBILITY"
    if any(kw in msg_lower for kw in ["deadline", "date", "time", "hours", "72 hours", "last date", "due date", "मुदत", "वेळ", "तास"]):
        return "DEADLINE"
    if any(kw in msg_lower for kw in ["next", "what next", "after this", "what should i do next", "पुढे काय", "आगे क्या"]):
        return "NEXT_STEP"
    if any(kw in msg_lower for kw in ["complaint", "grievance", "dispute", "appeal", "redressal", "तक्रार", "शिकायत"]):
        return "COMPLAINT"

    return "OVERVIEW"


# Backwards compatibility alias
_classify_intent = classify_intent
