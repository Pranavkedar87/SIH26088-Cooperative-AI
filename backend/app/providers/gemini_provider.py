"""
Gemini AI provider — Milestone 2 (real implementation).

Architecture:
    React → FastAPI /api/query → GeminiProvider → Gemini API → response

Security:
    - GEMINI_API_KEY is read from server-side .env only.
    - The key is NEVER passed to the frontend or included in any response.
    - Errors are logged server-side; users receive a safe generic message.
"""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from google import genai
from google.genai import types as genai_types

from app.config import get_settings
from app.providers.ai_provider import AIProvider
from app.schemas.query import IntentCode, QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

# ── Language display names ────────────────────────────────────────────────────

_LANG_NAME: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
}

# ── Fallback error answers per language ───────────────────────────────────────

_ERROR_ANSWER: dict[str, str] = {
    "en": (
        "I'm sorry, I'm unable to process your request right now. "
        "Please try again in a moment."
    ),
    "hi": (
        "क्षमा करें, मैं अभी आपका अनुरोध प्रक्रिया नहीं कर सकता। "
        "कृपया कुछ देर बाद पुनः प्रयास करें।"
    ),
    "mr": (
        "क्षमस्व, मला आत्ता तुमची विनंती प्रक्रिया करता येत नाही. "
        "कृपया थोड्या वेळाने पुन्हा प्रयत्न करा."
    ),
}

# ── System instruction ────────────────────────────────────────────────────────

_SYSTEM_INSTRUCTION = """You are Sahakari AI Sahayak (सहकारी AI सहाय्यक), a helpful and trustworthy multilingual cooperative governance assistant created for India's cooperative sector.

Your purpose is to assist cooperative society members, farmers, PACS members, and rural citizens by providing clear, simple, and accurate guidance about:
- Cooperative laws (especially Maharashtra Cooperative Societies Act and related state acts)
- Cooperative by-laws and governance
- Government cooperative schemes (PMFBY, KCC, etc.)
- Primary Agricultural Credit Societies (PACS)
- Agricultural support and subsidies
- Financial literacy for cooperative members
- Grievance redressal procedures for cooperative disputes
- General cooperative governance and management

LANGUAGE:
Always respond in the language specified in the request. Do not mix languages unnecessarily. Use clear, simple language appropriate for rural and semi-urban users.

IMPORTANT SAFETY RULES — Follow these strictly:
1. Do NOT invent or fabricate: laws, government schemes, eligibility criteria, application deadlines, fees, official procedures, government notifications, policy amendments, or citations.
2. Do NOT provide specific legal citations, section numbers, or clause references unless you are highly confident they are accurate.
3. Do NOT claim to have accessed a government database, official portal, or real-time source.
4. When your knowledge may be outdated or incomplete for a specific procedural question, clearly advise the user to verify through: the relevant Cooperative Department, NABARD, Ministry of Cooperation, or official government portals.
5. Do NOT perform or claim to perform any official government action (registration, application submission, etc.).
6. Be helpful and informative. Balance caution with usefulness — explain concepts clearly while flagging where official verification is needed.

RESPONSE STYLE:
- Use clear, structured responses with bullet points or numbered steps where appropriate.
- Keep answers concise but complete.
- For complex topics, provide a clear overview and then detail.
- Always be respectful and empathetic to the user's situation."""


# ── Intent classifier ─────────────────────────────────────────────────────────

# Maps keyword patterns → IntentCode.
# Evaluated in order; first match wins. Falls back to GENERAL_COOPERATIVE.
_INTENT_RULES: list[tuple[list[str], IntentCode]] = [
    (
        ["pmfby", "fasal bima", "फसल बीमा", "पीएमएफबीवाय", "पीएमएफबीवाई", "crop insurance",
         "pradhan mantri fasal", "पीक विमा", "पिक विमा", "soyabeen", "soybean", "सोयाबीन",
         "peek kharab", "पिक खराब", "पीक खराब", "paus", "pausa", "pavsa", "पाऊस", "पावसामुळे",
         "crop damage", "crop damaged", "rain damage"],
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
         "maharashtra cooperative", "mcs act", "section", "registration"],
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
         "ministry", "government scheme", "sarkar", "सरकार"],
        "MINISTRY_SCHEME",
    ),
    (
        ["crop loan", "agricultural loan", "farming loan", "farm loan", "agricultural support",
         "krishi", "कृषि", "शेती", "fertilizer", "seed", "peek", "पीक", "पिक", "kharab", "नुकसान"],
        "AGRICULTURAL_SUPPORT",
    ),
]



def _classify_intent(message: str) -> IntentCode:
    """
    Lightweight rule-based intent classification.
    Returns the first matching intent or GENERAL_COOPERATIVE.
    """
    msg_lower = message.lower()
    for keywords, intent in _INTENT_RULES:
        if any(kw in msg_lower for kw in keywords):
            return intent
    return "GENERAL_COOPERATIVE"


# ── Gemini provider ───────────────────────────────────────────────────────────

class GeminiProvider(AIProvider):
    """
    Concrete Gemini implementation of AIProvider (Milestone 2).

    Uses the official google-genai SDK.
    The client is initialized lazily on first use and cached as a singleton.
    """

    _client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        """Return a cached Gemini client, initializing it on first call."""
        if GeminiProvider._client is None:
            settings = get_settings()
            api_key = settings.gemini_api_key.strip()
            if not api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY is not set. "
                    "Add it to backend/.env and restart the server."
                )
            GeminiProvider._client = genai.Client(api_key=api_key)
            logger.info("Gemini client initialized.")
        return GeminiProvider._client

    def _build_prompt(
        self,
        message: str,
        language: str,
        intent: IntentCode,
    ) -> str:
        """Construct the user-turn prompt passed to Gemini."""
        lang_name = _LANG_NAME.get(language, "English")
        return (
            f"User language: {lang_name}\n"
            f"Detected intent: {intent}\n\n"
            f"User question:\n{message}\n\n"
            f"Please answer in {lang_name}."
        )

    async def answer_query(self, request: QueryRequest) -> QueryResponse:
        logger.info(
            "GeminiProvider.answer_query | lang=%s | intent_pre_classify | msg=%.80s",
            request.language,
            request.message,
        )

        # Step 1: classify intent
        intent = _classify_intent(request.message)
        logger.info("Classified intent: %s", intent)

        # Step 2: call Gemini
        try:
            client = self._get_client()
            prompt = self._build_prompt(request.message, request.language, intent)

            model_candidates = [
                "gemini-3.5-flash-lite",
                "gemini-3.5-flash",
                "gemini-3.6-flash",
                "gemini-2.5-flash",
            ]
            response = None
            for model_name in model_candidates:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=genai_types.GenerateContentConfig(
                            system_instruction=_SYSTEM_INSTRUCTION,
                            temperature=0.4,          # factual, low creativity
                            max_output_tokens=500,
                            safety_settings=[
                                genai_types.SafetySetting(
                                    category="HARM_CATEGORY_HARASSMENT",
                                    threshold="BLOCK_MEDIUM_AND_ABOVE",
                                ),
                                genai_types.SafetySetting(
                                    category="HARM_CATEGORY_HATE_SPEECH",
                                    threshold="BLOCK_MEDIUM_AND_ABOVE",
                                ),
                            ],
                        ),
                    )
                    if response and response.text:
                        break
                except Exception as exc:
                    logger.warning("GeminiProvider model '%s' skipped: %s", model_name, exc)
                    continue

            # Extract text safely
            answer = self._extract_text(response, request.language)

        except RuntimeError as exc:
            # Missing API key — configuration error
            logger.error("Configuration error: %s", exc)
            answer = _ERROR_ANSWER.get(request.language, _ERROR_ANSWER["en"])

        except Exception as exc:
            # Any Gemini API error, timeout, network issue, etc.
            logger.exception(
                "Gemini API error | lang=%s | intent=%s | error=%s",
                request.language,
                intent,
                type(exc).__name__,
            )
            answer = _ERROR_ANSWER.get(request.language, _ERROR_ANSWER["en"])

        return QueryResponse(
            answer=answer,
            language=request.language,
            intent=intent,
            source=None,
            next_action=None,
        )

    @staticmethod
    def _extract_text(response: object, language: str) -> str:
        """
        Safely extract plain text from the Gemini response object.
        Returns a user-friendly error message if extraction fails.
        """
        try:
            text = response.text  # type: ignore[attr-defined]
            if text and text.strip():
                return text.strip()
            logger.warning("Gemini returned empty text.")
            return _ERROR_ANSWER.get(language, _ERROR_ANSWER["en"])
        except Exception as exc:
            logger.error("Failed to extract Gemini response text: %s", exc)
            return _ERROR_ANSWER.get(language, _ERROR_ANSWER["en"])
