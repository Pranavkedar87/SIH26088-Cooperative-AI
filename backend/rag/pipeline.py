"""
Unified RAG + Web Research + Knowledge Router Pipeline powered by Groq AI Engine.

Architecture:
  User Query -> Session State Resolution -> Intent Classification & Topic Extraction -> Knowledge Router -> RAG Search / Web Research -> Groq Engine -> Display & Spoken Answers -> Telemetry
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any, Optional, Dict, List


def extract_json_payload(text: str) -> Optional[dict[str, Any]]:
    """Extracts and parses structured JSON object from LLM response text with auto-repair for truncated JSON."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # 1. Direct parse
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # 2. Extract largest matched JSON block
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    # 3. Resilient Repair for partially truncated JSON
    start_idx = cleaned.find("{")
    if start_idx != -1:
        partial = cleaned[start_idx:]
        for split_char in [",", "\n"]:
            subparts = partial.rsplit(split_char, 2)
            for sub in subparts[:-1]:
                cand = sub.strip()
                if cand.count('"') % 2 != 0:
                    cand += '"'
                open_brackets = max(0, cand.count('[') - cand.count(']'))
                open_braces = max(0, cand.count('{') - cand.count('}'))
                cand = cand + (']' * open_brackets) + ('}' * open_braces)
                try:
                    data = json.loads(cand)
                    if isinstance(data, dict):
                        return data
                except Exception:
                    continue

    return None

from app.config import get_settings
from app.providers.groq_provider import query_groq_llm, GROQ_MODELS
from app.providers.gemini_provider import query_gemini_llm
from app.providers.ollama_provider import query_ollama_llm, LOCAL_UNAVAILABLE_MESSAGE
from app.schemas.query import (
    IntentCode,
    QueryRequest,
    QueryResponse,
    SuggestedFollowup,
    StructuredAnswerPayload,
    AnswerSection,
    AnswerSectionItem,
)
from rag.intent import classify_intent, extract_topic_and_goal, extract_answer_focus
from rag.prompts import RAG_SYSTEM_INSTRUCTION, DIRECT_RESPONSES, NO_KNOWLEDGE_FALLBACK, NO_KNOWLEDGE_FALLBACK_WITH_STATE, get_intent_fallback
from rag.retriever import retrieve_relevant_knowledge, RetrievedChunk
from rag.router import route_query, RouterMode, RoutingDecision
from rag.session_state import (
    get_or_create_session,
    extract_slot_from_message,
    detect_pending_slot_from_answer,
    SessionState,
)
from rag.validator import (
    sanitize_source_citations,
    validate_and_sanitize_claims,
    evaluate_grounding_status,
)
from rag.web_search import search_web_knowledge

logger = logging.getLogger(__name__)


def clean_speech_text(text: str) -> str:
    """
    Strips markdown formatting, headings, bullet markers, URLs, citations, '::' artifacts,
    and legacy header prefixes for clean natural speech TTS audio playback.
    """
    if not text:
        return ""
    # Strip URLs
    cleaned = re.sub(r'https?://\S+', '', text)
    # Strip markdown headers, asterisks, underscores, backticks, hashes, bullet symbols
    cleaned = re.sub(r'#+\s*', '', cleaned)
    cleaned = re.sub(r'[\*\_\`]', '', cleaned)
    # Strip citation brackets e.g. [1], [Web-1], [Source: ...]
    cleaned = re.sub(r'\[\s*(?:web-)?\d+\s*\]', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
    # Strip leading bullet numbers/markers line by line
    cleaned = re.sub(r'^\s*[-*+•]\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*\d+[\.\)]\s+', '', cleaned, flags=re.MULTILINE)
    # Strip legacy heading prefixes and labels
    cleaned = re.sub(r'(?:Official Guidance|What Should I Do Now|Details|तुम्ही काय करू शकता|आप क्या करें):?', '', cleaned, flags=re.IGNORECASE)
    # Strip :: or leftover punctuation at start of text or line
    cleaned = re.sub(r'^[\s:]+', '', cleaned)
    cleaned = re.sub(r'::+', ' ', cleaned)
    # Collapse multiple whitespaces & newlines into clean natural speech spacing
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def generate_structured_answer(
    system_instruction: str,
    user_prompt: str,
    max_tokens: int = 2048,
) -> tuple[Optional[dict[str, Any]], str, dict[str, Any]]:
    """
    Primary synthesis generator based on configured AI_PROVIDER:
    - Default (AI_PROVIDER=ollama): Queries local Ollama instance (qwen3:8b).
      Gemini is NOT called.
    - If AI_PROVIDER=gemini: Queries Gemini API (with Groq fallback).
    """
    settings = get_settings()
    provider_name = (settings.ai_provider or "ollama").lower().strip()

    if provider_name == "ollama":
        raw_answer, used_model, ollama_stats = query_ollama_llm(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=0.2,
            response_format="json",
        )
        if raw_answer:
            payload = extract_json_payload(raw_answer)
            if payload and isinstance(payload, dict):
                logger.info(f"[PRIMARY LLM] provider=ollama model={used_model} status=SUCCESS (Structured JSON)")
                return payload, f"OLLAMA ({used_model})", ollama_stats

            # Wrap plain text or markdown response in structured schema
            wrapped = {
                "direct_answer": raw_answer.strip(),
                "sections": [],
                "spoken_answer": clean_speech_text(raw_answer)[:300],
            }
            logger.info(f"[PRIMARY LLM] provider=ollama model={used_model} status=SUCCESS (Plain text wrapped)")
            return wrapped, f"OLLAMA ({used_model})", ollama_stats

        logger.error(f"[PRIMARY LLM] provider=ollama model={settings.ollama_model} failed or is unavailable.")
        return None, "none", ollama_stats

    elif provider_name == "gemini":
        # 1. Try Gemini first
        raw_answer, used_model, gemini_stats = query_gemini_llm(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=0.2,
            response_mime_type="application/json",
        )
        if raw_answer:
            payload = extract_json_payload(raw_answer)
            if payload and isinstance(payload, dict):
                logger.info(f"[PRIMARY LLM] Structured output via Gemini ({used_model})")
                return payload, f"GEMINI ({used_model})", gemini_stats

            wrapped = {
                "direct_answer": raw_answer.strip(),
                "sections": [],
                "spoken_answer": clean_speech_text(raw_answer)[:300],
            }
            logger.info(f"[PRIMARY LLM] Plain text/markdown wrapped from Gemini ({used_model})")
            return wrapped, f"GEMINI ({used_model})", gemini_stats

        # 2. Groq fallback for gemini mode
        logger.warning("[PRIMARY LLM] Gemini failed — switching to Groq fallback")
        try:
            groq_answer, groq_model, groq_stats = query_groq_llm(
                system_instruction=system_instruction,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            if groq_answer:
                payload = extract_json_payload(groq_answer)
                if payload and isinstance(payload, dict):
                    logger.info(f"[FALLBACK LLM] Structured JSON from Groq ({groq_model})")
                    return payload, f"GROQ ({groq_model})", groq_stats

                wrapped = {
                    "direct_answer": groq_answer.strip(),
                    "sections": [],
                    "spoken_answer": clean_speech_text(groq_answer)[:300],
                }
                logger.info(f"[FALLBACK LLM] Plain text wrapped from Groq ({groq_model})")
                return wrapped, f"GROQ ({groq_model})", groq_stats
        except Exception as exc:
            logger.error(f"Groq fallback also failed: {exc}")

        return None, "none", {}

    return None, "none", {}


def generate_contextual_followups(
    intent: str,
    topic: Optional[str],
    answer_focus: str,
    language: str,
    message: str,
    llm_followups: Optional[list] = None,
) -> list[dict[str, str]]:
    """
    Produces 2 to 4 contextual follow-up questions tailored to the ongoing topic,
    answer_focus, and user's selected language.
    """
    lang = language.lower() if language in ["en", "hi", "mr"] else "en"

    # If LLM provided high quality followups with valid label & query, validate and sanitize
    if llm_followups and isinstance(llm_followups, list):
        sanitized = []
        for item in llm_followups:
            if isinstance(item, dict) and item.get("label") and item.get("query"):
                lbl = str(item["label"]).strip()
                qry = str(item["query"]).strip()
                if 2 <= len(lbl) <= 60 and len(qry) >= 5:
                    sanitized.append({"label": lbl, "query": qry})
            elif isinstance(item, str) and item.strip():
                lbl = item.strip()
                sanitized.append({"label": lbl, "query": lbl})
        if 2 <= len(sanitized) <= 4:
            return sanitized

    focus = (answer_focus or "OVERVIEW").upper()
    top = (topic or "").upper()
    intnt = (intent or "").upper()

    # 1. CROP INSURANCE / PMFBY
    if top == "CROP_INSURANCE" or intnt == "PMFBY":
        if focus == "OVERVIEW":
            if lang == "mr":
                return [
                    {"label": "मला कोणती कागदपत्रे लागतील?", "query": "पीएमएफबीवाय पीक नुकसान भरपाईसाठी आवश्यक कागदपत्रे कोणती आहेत?"},
                    {"label": "नुकसान नोंदवण्याची प्रक्रिया काय आहे?", "query": "पीएमएफबीवाय पीक नुकसान नोंदणीची अधिकृत टप्पा-निहाय प्रक्रिया काय आहे?"},
                    {"label": "अधिकृत संपर्क व हेल्पलाईन काय आहे?", "query": "पीएमएफबीवाय पीक विम्यासंदर्भात अधिकृत हेल्पलाइन नंबर आणि संपर्क तपशील काय आहेत?"},
                ]
            elif lang == "hi":
                return [
                    {"label": "मुझे कौन से दस्तावेज चाहिए?", "query": "पीएमएफबीवाई फसल नुकसान रिपोर्टिंग के लिए कौन से आवश्यक दस्तावेज हैं?"},
                    {"label": "फसल नुकसान की प्रक्रिया क्या है?", "query": "पीएमएफबीवाई के तहत फसल नुकसान दर्ज करने की चरण-दर-चरण प्रक्रिया क्या है?"},
                    {"label": "आधिकारिक हेल्पलाइन नंबर क्या है?", "query": "पीएमएफबीवाई फसल बीमा के लिए आधिकारिक हेल्पलाइन और संपर्क विवरण क्या हैं?"},
                ]
            else:
                return [
                    {"label": "What documents do I need?", "query": "What documents do I need for PMFBY crop damage reporting?"},
                    {"label": "What is the reporting procedure?", "query": "What is the official procedure for PMFBY crop damage reporting?"},
                    {"label": "Who should I contact?", "query": "Who are the official PMFBY helpline and contact authorities?"},
                ]
        elif focus == "DOCUMENTS":
            if lang == "mr":
                return [
                    {"label": "अर्जाची प्रक्रिया काय आहे?", "query": "पीएमएफबीवाय अंतर्गत अर्ज किंवा नुकसान भरपाईची टप्पा-निहाय प्रक्रिया काय आहे?"},
                    {"label": "नुकसान नोंदवण्याची मुदत किती आहे?", "query": "नैसर्गिक आपत्तीनंतर पीक नुकसान नोंदवण्याची अधिकृत मुदत काय आहे?"},
                    {"label": "कागदपत्रे कुठे जमा करावीत?", "query": "पीक विम्याची कागदपत्रे कोठे आणि कोणाकडे जमा करावी लागतात?"},
                ]
            elif lang == "hi":
                return [
                    {"label": "आवेदन की प्रक्रिया क्या है?", "query": "पीएमएफबीवाई के तहत फसल बीमा क्लेम की चरण-दर-चरण प्रक्रिया क्या है?"},
                    {"label": "नुकसान रिपोर्ट करने की समय सीमा क्या है?", "query": "प्राकृतिक आपदा के बाद फसल नुकसान रिपोर्ट करने की आधिकारिक समय सीमा क्या है?"},
                    {"label": "दस्तावेज कहाँ जमा करें?", "query": "फसल बीमा क्लेम के दस्तावेज कहाँ और किसके पास जमा करने होते हैं?"},
                ]
            else:
                return [
                    {"label": "What is the application procedure?", "query": "What is the step-by-step procedure for PMFBY claim submission?"},
                    {"label": "What is the reporting deadline?", "query": "What is the official deadline for reporting PMFBY localized crop damage?"},
                    {"label": "Where should I submit documents?", "query": "Where and to whom should I submit PMFBY claim documents?"},
                ]
        elif focus == "PROCEDURE":
            if lang == "mr":
                return [
                    {"label": "आवश्यक कागदपत्रांची यादी द्या", "query": "पीएमएफबीवाय पीक नुकसान भरपाईसाठी आवश्यक कागदपत्रांची चेकलिस्ट काय आहे?"},
                    {"label": "नुकसान भरपाईची मुदत किती आहे?", "query": "पीक नुकसान झाल्यानंतर किती तासांत सूचना देणे बंधनकारक आहे?"},
                    {"label": "स्थानिक अधिकारी कोण आहेत?", "query": "पीक विमा तक्रार किंवा मंजुरीसाठी स्थानिक तालुका कृषी अधिकारी व विमा प्रतिनिधी कोण आहेत?"},
                ]
            elif lang == "hi":
                return [
                    {"label": "आवश्यक दस्तावेजों की सूची दें", "query": "पीएमएफबीवाई क्लेम के लिए कौन-कौन से आवश्यक दस्तावेज तैयार रखने चाहिए?"},
                    {"label": "सूचना देने की समय सीमा क्या है?", "query": "फसल खराब होने के कितने समय के भीतर सूचना देना आवश्यक है?"},
                    {"label": "स्थानीय कृषि अधिकारी कौन हैं?", "query": "पीएमएफबीवाई सहायता के लिए स्थानीय कृषि अधिकारी या बीमा कंपनी से कैसे संपर्क करें?"},
                ]
            else:
                return [
                    {"label": "What documents do I need?", "query": "What is the required document checklist for PMFBY crop loss claims?"},
                    {"label": "What is the reporting deadline?", "query": "What is the deadline within which crop damage must be reported under PMFBY?"},
                    {"label": "Who should I contact locally?", "query": "Who is the local district agriculture officer or insurance representative for PMFBY?"},
                ]
        elif focus == "CONTACT":
            if lang == "mr":
                return [
                    {"label": "अर्जाची टप्पा-निहाय प्रक्रिया काय आहे?", "query": "पीएमएफबीवाय क्लेम दाखल करण्याची संपूर्ण प्रक्रिया काय आहे?"},
                    {"label": "कोणती कागदपत्रे सोबत ठेवावीत?", "query": "पीक विमा संपर्क करताना कोणती कागदपत्रे सोबत असणे आवश्यक आहे?"},
                ]
            elif lang == "hi":
                return [
                    {"label": "दावा करने की प्रक्रिया क्या है?", "query": "पीएमएफबीवाई क्लेम दर्ज करने की पूरी चरण-दर-चरण प्रक्रिया क्या है?"},
                    {"label": "कौन से दस्तावेज तैयार रखें?", "query": "फसल बीमा क्लेम के लिए कौन से दस्तावेज तैयार रखने चाहिए?"},
                ]
            else:
                return [
                    {"label": "What is the claim procedure?", "query": "What is the step-by-step procedure to file a PMFBY crop insurance claim?"},
                    {"label": "What documents should I keep ready?", "query": "What documents should I keep ready when contacting the PMFBY authority?"},
                ]

    # 2. PACS SERVICE / MEMBERSHIP
    if top == "PACS_MEMBERSHIP" or intnt == "PACS_SERVICE":
        if lang == "mr":
            return [
                {"label": "पीक कर्जासाठी कसा अर्ज करावा?", "query": "पॅक्स (PACS) मधून अल्पमुदत पीक कर्ज (KCC) मिळवण्यासाठी कसा अर्ज करावा?"},
                {"label": "पॅक्स सदस्यत्वासाठी कागदपत्रे काय आहेत?", "query": "पॅक्स (PACS) चे सभासद होण्यासाठी कोणती कागदपत्रे आणि पात्रता लागते?"},
                {"label": "पॅक्समध्ये इतर कोणत्या सेवा मिळतात?", "query": "पॅक्स (PACS) मध्ये खते, बी-बियाणे आणि कृषी अवजारांच्या कोणत्या सेवा मिळतात?"},
            ]
        elif lang == "hi":
            return [
                {"label": "फसल ऋण के लिए कैसे आवेदन करें?", "query": "पैक्स (PACS) से अल्पकालिक फसल ऋण (KCC) के लिए कैसे आवेदन करें?"},
                {"label": "पैक्स सदस्यता के लिए दस्तावेज क्या हैं?", "query": "पैक्स (PACS) सदस्य बनने के लिए कौन से दस्तावेज और पात्रता आवश्यक है?"},
                {"label": "पैक्स में कौन-कौन सी सेवाएं उपलब्ध हैं?", "query": "पैक्स (PACS) में खाद, बीज और कृषि उपकरणों की कौन सी सेवाएं मिलती हैं?"},
            ]
        else:
            return [
                {"label": "How can I apply for a crop loan?", "query": "How can an active PACS member apply for a KCC short-term crop loan?"},
                {"label": "What documents are required?", "query": "What documents and eligibility are required for PACS membership and loans?"},
                {"label": "What other services are available at PACS?", "query": "What agricultural inputs, warehousing, and custom hiring services are available at PACS?"},
            ]

    # 3. TRACTOR / AGRICULTURAL MECHANIZATION SUBSIDY
    if top == "TRACTOR_PURCHASE" or (intnt == "MINISTRY_SCHEME" and any(k in message.lower() for k in ["tractor", "machin", "अवजार", "ट्रॅक्टर", "ट्रैक्टर", "यंत्र"])):
        if lang == "mr":
            return [
                {"label": "ट्रॅक्टर अनुदानासाठी कागदपत्रे काय लागतात?", "query": "महाडीबीटी / SMAM अंतर्गत ट्रॅक्टर व कृषी अवजारे अनुदानासाठी आवश्यक कागदपत्रे काय आहेत?"},
                {"label": "ऑनलाइन अर्ज कसा करावा?", "query": "महाडीबीटी पोर्टलवर ट्रॅक्टर अनुदानासाठी ऑनलाइन अर्ज करण्याची टप्पा-निहाय प्रक्रिया काय आहे?"},
                {"label": "अनुदान किती टक्के मिळते?", "query": "लहान, अत्यल्प भूधारक व महिला शेतकऱ्यांसाठी ट्रॅक्टरवर किती टक्के अनुदान मिळते?"},
            ]
        elif lang == "hi":
            return [
                {"label": "ट्रैक्टर सब्सिडी के लिए दस्तावेज क्या हैं?", "query": "कृषि यंत्रीकरण (SMAM) के तहत ट्रैक्टर सब्सिडी के लिए कौन से दस्तावेज चाहिए?"},
                {"label": "आवेदन की प्रक्रिया क्या है?", "query": "ट्रैक्टर सब्सिडी योजना के लिए ऑनलाइन आवेदन की चरण-दर-चरण प्रक्रिया क्या है?"},
                {"label": "सब्सिडी की पात्रता क्या है?", "query": "ट्रैक्टर और कृषि यंत्र सब्सिडी के लिए पात्रता और अनुदान प्रतिशत क्या है?"},
            ]
        else:
            return [
                {"label": "What documents are required?", "query": "What documents are needed to apply for tractor and machinery subsidy under SMAM / MahaDBT?"},
                {"label": "What is the application process?", "query": "What is the step-by-step application procedure for tractor subsidy on official government portals?"},
                {"label": "What are the eligibility criteria?", "query": "What are the eligibility criteria and subsidy percentage for agricultural mechanization?"},
            ]

    # 4. GRIEVANCE REDRESSAL
    if intnt == "GRIEVANCE":
        if lang == "mr":
            return [
                {"label": "तक्रार कोणाकडे करावी?", "query": "सहकारी संस्थेच्या अन्यायाविरुद्ध जिल्हा उपनिबंधक (DDR) यांच्याकडे तक्रार कशी करावी?"},
                {"label": "तक्रारीसोबत कोणती कागदपत्रे जोडावीत?", "query": "सहकारी तक्रार अर्जासोबत कोणते पुरावे व कागदपत्रे जोडणे आवश्यक आहे?"},
                {"label": "सहकारी न्यायालयाचे नियम काय आहेत?", "query": "सहकारी वादावर दाद मागण्यासाठी सहकारी न्यायालयाची प्रक्रिया काय आहे?"},
            ]
        elif lang == "hi":
            return [
                {"label": "शिकायत किस अधिकारी से करें?", "query": "सहकारी संस्था के खिलाफ जिला उप-निबंधक (DDR) के पास शिकायत कैसे दर्ज करें?"},
                {"label": "शिकायत के लिए कौन से दस्तावेज चाहिए?", "query": "सहकारी शिकायत दर्ज करने के लिए कौन से साक्ष्य और दस्तावेज संलग्न करने चाहिए?"},
                {"label": "शिकायत निवारण की प्रक्रिया क्या है?", "query": "सहकारी विवादों के कानूनी निवारण की चरण-दर-चरण प्रक्रिया क्या है?"},
            ]
        else:
            return [
                {"label": "Which authority should I approach?", "query": "Which cooperative authority or District Deputy Registrar (DDR) should I approach for grievances?"},
                {"label": "How can I prepare a formal complaint?", "query": "How should I draft and submit a formal written complaint against a cooperative society?"},
                {"label": "What supporting documents are needed?", "query": "What evidence and supporting documents should be attached with a cooperative grievance?"},
            ]

    # 5. FINANCIAL LITERACY & CREDIT MANAGEMENT
    if intnt == "FINANCIAL_LITERACY":
        if lang == "mr":
            return [
                {"label": "KCC पीक कर्जाचे फायदे काय आहेत?", "query": "किसान क्रेडिट कार्ड (KCC) पीक कर्जावरील व्याज सवलत आणि फायदे काय आहेत?"},
                {"label": "शेतकऱ्यांनी कर्ज व्यवस्थापन कसे करावे?", "query": "शेतकरी सभासदांनी योग्य आर्थिक नियोजन आणि वेळेवर कर्ज परतफेडीचे व्यवस्थापन कसे करावे?"},
                {"label": "सरकारी बचत व विमा योजना कोणत्या आहेत?", "query": "ग्रामीण शेतकऱ्यांसाठी फायदेशीर सरकारी बचत आणि पेन्शन योजना कोणत्या आहेत?"},
            ]
        elif lang == "hi":
            return [
                {"label": "KCC फसल ऋण के लाभ क्या हैं?", "query": "किसान क्रेडिट कार्ड (KCC) फसल ऋण पर मिलने वाली ब्याज सब्सिडी और लाभ क्या हैं?"},
                {"label": "कृषि ऋण प्रबंधन कैसे करें?", "query": "किसानों के लिए वित्तीय योजना और समय पर ऋण चुकाने के सर्वोत्तम तरीके क्या हैं?"},
                {"label": "सरकारी बचत योजनाएं कौन सी हैं?", "query": "ग्रामीण किसानों के लिए उपलब्ध सरकारी बचत और सामाजिक सुरक्षा योजनाएं कौन सी हैं?"},
            ]
        else:
            return [
                {"label": "What is KCC loan benefit?", "query": "What are the interest subvention and financial benefits under Kisan Credit Card (KCC)?"},
                {"label": "How can farmers manage credit?", "query": "What are the best financial management practices for cooperative members taking agricultural loans?"},
                {"label": "What savings schemes exist?", "query": "What government rural savings, insurance, and pension schemes are available for farmers?"},
            ]

    # 6. UNIVERSAL CONTEXTUAL FALLBACK (General knowledge, science, schemes)
    clean_msg = message[:35].strip()
    if lang == "mr":
        return [
            {"label": "याबद्दल अधिक सोप्या भाषेत सांगा", "query": f"'{clean_msg}' बद्दल अधिक सोप्या आणि मुद्देसूद भाषेत स्पष्ट करा."},
            {"label": "याची महत्त्वाची उदाहरणे काय आहेत?", "query": f"'{clean_msg}' चे मुख्य उपयोग आणि व्यावहारिक उदाहरणे काय आहेत?"},
            {"label": "पुढील माहिती काय आहे?", "query": f"'{clean_msg}' संदर्भात पुढील महत्त्वाची माहिती व मार्गदर्शन काय आहे?"},
        ]
    elif lang == "hi":
        return [
            {"label": "इसे और सरल शब्दों में समझाएं", "query": f"'{clean_msg}' को और सरल व स्पष्ट शब्दों में समझाएं."},
            {"label": "इसके मुख्य उदाहरण क्या हैं?", "query": f"'{clean_msg}' के मुख्य व्यावहारिक उदाहरण और उपयोग क्या हैं?"},
            {"label": "इसके बारे में और बताएं", "query": f"'{clean_msg}' से संबंधित अन्य महत्वपूर्ण जानकारी क्या है?"},
        ]
    else:
        return [
            {"label": "Explain in simpler terms", "query": f"Can you explain '{clean_msg}' in simpler terms with key takeaways?"},
            {"label": "What are practical examples?", "query": f"What are practical examples and applications for '{clean_msg}'?"},
            {"label": "What should I know next?", "query": f"What are the most important next steps or related concepts for '{clean_msg}'?"},
        ]


class RAGPipeline:
    """Orchestrates end-to-end grounded query answering using Gemini Primary with Groq Fallback Engine."""

    async def process_query(self, request: QueryRequest) -> tuple[QueryResponse, list[dict[str, Any]]]:
        """
        Process user query through Unified Intelligence Engine with conversational slot resolution.
        """
        request_start = time.perf_counter()
        message = request.message.strip()
        session_id = request.session_id or "default-session"
        detected_language = request.language or "en"
        response_language = detected_language
        tts_language = detected_language
        resp_mode = getattr(request, "response_mode", "text") or "text"

        # Stage 1: Conversational Session State Manager
        session = get_or_create_session(session_id)
        session.turn_number += 1
        pending_slot_before = session.pending_slot

        # Slot Extraction from message
        extracted_slot_name, extracted_slot_val = extract_slot_from_message(message, pending_slot_before)
        extracted_slot = f"{extracted_slot_name}:{extracted_slot_val}" if extracted_slot_name else None
        context_used = False

        if extracted_slot_name and extracted_slot_val:
            session.collected_slots[extracted_slot_name] = extracted_slot_val
            session.pending_slot = None  # Resolved!
            context_used = True

        # Stage 2: Intent Classification & Topic/Goal Extraction
        intent_start = time.perf_counter()
        # Stage 2: Intent Classification & Topic/Goal Extraction
        intent_start = time.perf_counter()
        raw_intent = classify_intent(message)
        extracted_topic, extracted_goal = extract_topic_and_goal(message)
        answer_focus = extract_answer_focus(message)
        intent_latency_ms = (time.perf_counter() - intent_start) * 1000.0

        # Contextual Follow-up Detection Logic
        followup_keywords = [
            "document", "documents", "land", "record", "records", "proof", "paper", "papers",
            "procedure", "process", "step", "steps", "how", "what", "where", "deadline", "date",
            "time", "hours", "contact", "helpline", "number", "office", "authority", "form", "apply",
            "status", "claim", "money", "payout", "compensation", "eligibility", "criteria", "fee",
            "cost", "which", "can i", "do i", "need", "required", "kaun", "kya", "kaise",
            "कागदपत्रे", "पुरावे", "प्रक्रिया", "संपर्क", "हेल्पलाईन", "दस्तावेज", "प्रमाण", "हेल्पलाइन",
            "नुकसान", "पिक", "बीमा", "विमा", "अर्जाची"
        ]

        msg_lower = message.lower()
        has_followup_kw = any(kw in msg_lower for kw in followup_keywords)

        is_contextual_followup = (
            bool(session.topic) and
            session.topic != "GENERAL_COOPERATIVE_QUERY" and
            len(session.history) > 0 and
            has_followup_kw and
            extracted_topic == "GENERAL_COOPERATIVE_QUERY"
        )

        if extracted_topic != "GENERAL_COOPERATIVE_QUERY":
            # Explicit domain topic switch (e.g. user asks about tractor or pacs explicitly)
            session.topic = extracted_topic
            session.user_goal = extracted_goal
            intent = raw_intent
        elif is_contextual_followup:
            # Preserve session topic for contextual follow-up turn
            context_used = True
            if session.topic == "CROP_INSURANCE":
                intent = "PMFBY"
            elif session.topic == "PACS_MEMBERSHIP":
                intent = "PACS_SERVICE"
            elif session.topic == "TRACTOR_PURCHASE":
                intent = "MINISTRY_SCHEME"
            elif session.topic == "AGRICULTURAL_LOAN":
                intent = "AGRICULTURAL_SUPPORT"
            else:
                intent = raw_intent
        else:
            # Topic reset for independent non-domain query (e.g., "Who is the Prime Minister of India?")
            if session.history and not has_followup_kw:
                session.topic = None
                session.user_goal = None
            intent = raw_intent

        current_topic = session.topic or extracted_topic
        current_goal = session.user_goal or extracted_goal

        # Stage 3: Pre-Retrieval Knowledge Router
        router_start = time.perf_counter()
        routing_decision = route_query(message, intent)
        router_mode = routing_decision.mode
        router_latency_ms = (time.perf_counter() - router_start) * 1000.0

        # Stage 4 + 5: RAG retrieval AND Web Search run IN PARALLEL for speed
        rag_start = time.perf_counter()

        # Build effective search query for RAG + web
        if is_contextual_followup and session.topic:
            topic_query_prefix = session.topic
            if session.topic == "CROP_INSURANCE":
                topic_query_prefix = "PMFBY crop insurance"
            elif session.topic == "PACS_MEMBERSHIP":
                topic_query_prefix = "PACS cooperative society"
            elif session.topic == "TRACTOR_PURCHASE":
                topic_query_prefix = "SMAM tractor subsidy scheme"
            effective_search_query = f"{topic_query_prefix} {answer_focus.lower()} {message}"
        else:
            effective_search_query = message

        if session.collected_slots.get("state"):
            effective_search_query += f" {session.collected_slots.get('state')}"

        async def _fetch_rag() -> list:
            if not routing_decision.trigger_rag:
                return []
            try:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(
                    None,
                    lambda: retrieve_relevant_knowledge(
                        query=effective_search_query,
                        language=detected_language,
                        intent=intent,
                        top_k=3,
                        match_threshold=0.45,
                    )
                )
            except Exception as exc:
                logger.error("Knowledge retrieval exception: %s", exc)
                return []

        async def _fetch_web() -> list:
            # Only trigger web search when router explicitly requests it
            if not routing_decision.trigger_web:
                return []
            try:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(
                    None,
                    lambda: search_web_knowledge(effective_search_query, max_results=2)
                )
            except Exception as exc:
                logger.warning(f"Web search execution exception: {exc}")
                return []

        # Run RAG + web search concurrently
        rag_chunks, web_results = await asyncio.gather(_fetch_rag(), _fetch_web())
        rag_latency_ms = (time.perf_counter() - rag_start) * 1000.0
        web_search_latency_ms = rag_latency_ms  # both ran in parallel

        # Stage 6: Extract and combine verified source citations with Authority Levels
        sources_list: list[dict[str, Any]] = []
        rag_source_titles: list[str] = []
        web_source_urls: list[str] = []
        seen_urls = set()

        for chunk in rag_chunks:
            title = chunk.get("title") or "Official Knowledge Base"
            url = chunk.get("source_url") or ""
            rag_source_titles.append(title)
            if title not in seen_urls:
                seen_urls.add(title)
                sources_list.append({
                    "title": title,
                    "source_name": chunk.get("source_name") or "Cooperative DB",
                    "source_url": url,
                    "document_id": chunk.get("document_id"),
                })

        for web_item in web_results:
            url = web_item.get("source_url") or ""
            web_source_urls.append(url or web_item.get("source_name", "web_source"))
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources_list.append({
                    "title": web_item.get("title") or "Live Government Notice",
                    "source_name": web_item.get("source_name") or "Government Web Portal",
                    "source_url": url,
                    "document_id": None,
                    "authority_level": web_item.get("authority_level", "GENERAL"),
                })

        sources_list = sanitize_source_citations(sources_list, is_legal_or_gov_query=True)
        primary_source = sources_list[0]["title"] if sources_list else "SahkaarSetu Cooperative Guidance"

        # Stage 7: Construct Grounded Prompt for Gemini AI Engine
        prompt_start = time.perf_counter()
        context_parts = []
        if rag_chunks:
            context_parts.append("--- OFFICIAL GROUNDED RAG KNOWLEDGE BASE ---")
            for idx, chunk in enumerate(rag_chunks, 1):
                context_parts.append(f"[{idx}] {chunk.get('title')}: {chunk.get('content')}")

        if web_results:
            context_parts.append("--- LIVE AUTHORITATIVE WEB RESEARCH SOURCES ---")
            for idx, item in enumerate(web_results, 1):
                auth_tag = f"[{item.get('authority_level', 'GENERAL')}]"
                context_parts.append(f"[Web-{idx}]{auth_tag} {item.get('title')} ({item.get('source_name')}): {item.get('snippet')}")

        if not context_parts:
            context_parts.append("NO SPECIFIC GROUNDING CONTEXT RETRIEVED. Use your general knowledge to answer the user's question accurately and completely.")

        combined_context = "\n".join(context_parts)

        lang_names = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
        target_lang = lang_names.get(detected_language, "English")

        system_instruction = RAG_SYSTEM_INSTRUCTION
        user_prompt = (
            f"ORIGINAL USER QUESTION: {message}\n"
            f"STRICT RESPONSE LANGUAGE: {target_lang}\n"
            f"Detected Intent: {intent}\n"
            f"Answer Focus: {answer_focus}\n"
            f"Active Session Turn: {session.turn_number}\n"
        )

        if session.history:
            history_lines = [f"{h['role'].upper()}: {h['content']}" for h in session.history[-4:]]
            user_prompt += f"\nPREVIOUS CONVERSATION HISTORY:\n" + "\n".join(history_lines) + "\n"

        user_prompt += (
            f"\nOFFICIAL GROUNDED CONTEXT:\n{combined_context}\n\n"
            f"STRICT INSTRUCTION: Answer the user's EXACT ORIGINAL QUESTION ('{message}') in {target_lang}. "
            f"If grounded context is available and relevant, use it. "
            f"If the question is general knowledge, science, history, technology, or any other topic, "
            f"answer from your own knowledge directly and completely. "
            f"Do NOT restrict yourself to cooperative or agricultural topics only. "
        )

        if is_contextual_followup:
            user_prompt += (
                f"\n\n--- MULTI-TURN CONTEXT RESOLUTION & ANSWER FOCUS ---\n"
                f"Active Conversation Topic: {session.topic or intent}\n"
                f"Requested Answer Focus: {answer_focus}\n"
                f"CRITICAL MULTI-TURN INSTRUCTION:\n"
                f"The user is asking a SPECIFIC FOLLOW-UP question ('{message}') focused on '{answer_focus}' for the ongoing topic '{session.topic or intent}'.\n"
                f"DO NOT repeat the previous broad overview answer from conversation history!\n"
                f"DO NOT include greetings on follow-up turns.\n"
                f"Generate a NEW, highly focused answer specifically concentrating on '{answer_focus}'.\n"
            )
            if answer_focus == "PROCEDURE":
                user_prompt += "Focus heavily on listing the exact 1, 2, 3 numbered step-by-step procedural steps under 'what_should_i_do_now' and 'summary'.\n"
            elif answer_focus == "DOCUMENTS":
                user_prompt += "Focus heavily on listing the required land records (7/12 extract, 8A), proofs, bank passbook, and application documents.\n"
            elif answer_focus == "CONTACT":
                user_prompt += "Focus heavily on providing official helpline numbers, toll-free contacts, portal URLs (pmfby.gov.in), and local authorities (DDR / District Agriculture Officer).\n"
            elif answer_focus == "NEXT_STEP":
                user_prompt += "Focus heavily on what immediate next practical step the user must execute right now.\n"
        else:
            if session.turn_number == 1:
                user_prompt += f"\nInclude a brief, warm greeting at the beginning of 'summary' (e.g. 'Hello! Welcome to SahkaarSetu.'). Generate dynamic, question-specific action points or key details under 'what_should_i_do_now' matching '{answer_focus}'."
            else:
                user_prompt += f"\nDo NOT include greetings. Generate dynamic, question-specific action points under 'what_should_i_do_now' matching '{answer_focus}'."

        # Context-resolution guidance when state is already collected
        if session.collected_slots.get("state"):
            st_val = session.collected_slots.get("state")
            user_prompt += (
                f"\n\nCRITICAL CONVERSATIONAL STATE INSTRUCTION:\n"
                f"The user has ALREADY provided state = '{st_val}'.\n"
                f"Do NOT ask 'Which state are you from?' or repeat generic questions under any circumstances!\n"
                f"Provide state-specific guidance for '{st_val}' (e.g. MahaDBT / Agricultural Mechanization / SMAM subsidy application portal) "
                f"and outline the next actionable step (e.g. document requirements or application website).\n"
            )
        elif current_topic == "TRACTOR_PURCHASE" and not session.collected_slots.get("state"):
            user_prompt += (
                "\n\nTRACTOR SCHEME MISSING STATE INSTRUCTION:\n"
                "Explain generally that tractor subsidies exist under SMAM & State Agriculture Departments, and end by asking: 'Which state are you from?'\n"
            )

        if resp_mode == "voice":
            user_prompt += (
                f"\n\nVOICE MODE INSTRUCTIONS:\n"
                f"Output valid JSON matching the schema. "
                f"Set 'spoken_answer' to 1 to 2 conversational, natural sentences in {target_lang} for voice TTS playback (no markdown, no bullets). "
                f"Keep structured sections concise and directly relevant."
            )

        prompt_build_latency_ms = (time.perf_counter() - prompt_start) * 1000.0

        # Stage 8: Call Provider-Agnostic LLM Engine (Gemini Primary -> Groq Fallback)
        max_tokens = 2048
        json_payload, used_model, llm_stats = generate_structured_answer(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )

        # Stage 8.5: Canonical Response Ingestion & Grounding Validation Stage
        structured_payload: Optional[StructuredAnswerPayload] = None

        if json_payload and isinstance(json_payload, dict):
            disp_obj = json_payload.get("display_answer") if isinstance(json_payload.get("display_answer"), dict) else json_payload

            # 1. Extract Direct Answer
            direct_answer = (
                json_payload.get("direct_answer")
                or disp_obj.get("direct_answer")
                or disp_obj.get("summary")
                or disp_obj.get("title")
                or json_payload.get("answer")
                or disp_obj.get("answer")
                or json_payload.get("message")
                or disp_obj.get("message")
                or ""
            ).strip()

            # 2. Extract Sections
            sections_raw = json_payload.get("sections") or disp_obj.get("sections")
            parsed_sections: list[AnswerSection] = []

            if sections_raw and isinstance(sections_raw, list):
                for sec in sections_raw:
                    if isinstance(sec, dict) and sec.get("type"):
                        sec_type = str(sec["type"]).lower().strip()
                        sec_title = str(sec.get("title") or "").strip()
                        raw_items = sec.get("items") or []
                        sec_items = []
                        if isinstance(raw_items, list):
                            for itm in raw_items:
                                if isinstance(itm, dict):
                                    sec_items.append(AnswerSectionItem(
                                        title=itm.get("title"),
                                        description=itm.get("description") or itm.get("content"),
                                        name=itm.get("name"),
                                        label=itm.get("label"),
                                        value=itm.get("value"),
                                        content=itm.get("content"),
                                    ))
                                elif isinstance(itm, str) and itm.strip():
                                    sec_items.append(AnswerSectionItem(title=itm.strip()))
                        parsed_sections.append(AnswerSection(
                            type=sec_type,
                            title=sec_title,
                            items=sec_items,
                            content=sec.get("content"),
                        ))
            else:
                # Dynamic normalization for root-level keys (steps, documents, key_facts, where_to_go, helpline, etc.)
                steps_data = (
                    disp_obj.get("steps")
                    or disp_obj.get("action_steps")
                    or disp_obj.get("what_should_i_do_now")
                    or json_payload.get("steps")
                )
                if steps_data and isinstance(steps_data, list):
                    action_title = (
                        "What You Should Do" if detected_language == "en"
                        else "काय करावे?" if detected_language == "mr"
                        else "क्या करें?"
                    )
                    items = []
                    for idx, act in enumerate(steps_data, 1):
                        if isinstance(act, dict):
                            items.append(AnswerSectionItem(
                                title=act.get("title") or act.get("name") or f"Step {idx}",
                                description=act.get("description") or act.get("content") or "",
                            ))
                        elif isinstance(act, str) and act.strip():
                            items.append(AnswerSectionItem(title=act.strip()))
                    if items:
                        parsed_sections.append(AnswerSection(
                            type="steps",
                            title=action_title,
                            items=items,
                        ))

                docs_data = (
                    disp_obj.get("documents")
                    or disp_obj.get("required_documents")
                    or disp_obj.get("documents_required")
                    or json_payload.get("documents")
                )
                if docs_data and isinstance(docs_data, list):
                    doc_title = (
                        "Required Documents" if detected_language == "en"
                        else "आवश्यक कागदपत्रे" if detected_language == "mr"
                        else "आवश्यक दस्तावेज"
                    )
                    items = []
                    for itm in docs_data:
                        if isinstance(itm, dict):
                            items.append(AnswerSectionItem(
                                name=itm.get("name") or itm.get("title"),
                                description=itm.get("description") or itm.get("content"),
                            ))
                        elif isinstance(itm, str) and itm.strip():
                            items.append(AnswerSectionItem(name=itm.strip()))
                    if items:
                        parsed_sections.append(AnswerSection(
                            type="documents",
                            title=doc_title,
                            items=items,
                        ))

                facts_data = disp_obj.get("key_facts") or json_payload.get("key_facts")
                if facts_data and isinstance(facts_data, list):
                    fact_title = (
                        "Key Facts" if detected_language == "en"
                        else "महत्त्वाची माहिती" if detected_language == "mr"
                        else "महत्वपूर्ण तथ्य"
                    )
                    items = []
                    for itm in facts_data:
                        if isinstance(itm, dict):
                            items.append(AnswerSectionItem(
                                label=itm.get("label") or itm.get("title"),
                                value=itm.get("value") or itm.get("content") or itm.get("description"),
                            ))
                        elif isinstance(itm, str) and itm.strip():
                            items.append(AnswerSectionItem(label=itm.strip()))
                    if items:
                        parsed_sections.append(AnswerSection(
                            type="key_facts",
                            title=fact_title,
                            items=items,
                        ))

                channels_data = (
                    disp_obj.get("where_to_go")
                    or disp_obj.get("helpline")
                    or disp_obj.get("channels")
                    or disp_obj.get("where_to_apply")
                    or json_payload.get("where_to_go")
                    or json_payload.get("helpline")
                )
                if channels_data:
                    chan_title = (
                        "Where to Go / Contact" if detected_language == "en"
                        else "कुठे संपर्क साधावा?" if detected_language == "mr"
                        else "कहाँ संपर्क करें?"
                    )
                    if isinstance(channels_data, list):
                        items = []
                        for itm in channels_data:
                            if isinstance(itm, dict):
                                items.append(AnswerSectionItem(
                                    name=itm.get("name") or itm.get("title"),
                                    description=itm.get("description") or itm.get("content"),
                                ))
                            elif isinstance(itm, str) and itm.strip():
                                items.append(AnswerSectionItem(name=itm.strip()))
                        if items:
                            parsed_sections.append(AnswerSection(
                                type="where_to_go",
                                title=chan_title,
                                items=items,
                            ))
                    elif isinstance(channels_data, str) and channels_data.strip():
                        parsed_sections.append(AnswerSection(
                            type="where_to_go",
                            title=chan_title,
                            content=channels_data.strip(),
                        ))

                if disp_obj.get("detailed_information") or disp_obj.get("details"):
                    det_content = str(disp_obj.get("detailed_information") or disp_obj.get("details") or "").strip()
                    if det_content:
                        parsed_sections.append(AnswerSection(
                            type="details",
                            title="Details" if detected_language == "en" else "तपशील" if detected_language == "mr" else "विवरण",
                            content=det_content,
                        ))

                if disp_obj.get("next_guidance") or disp_obj.get("next_action"):
                    nxt_content = str(disp_obj.get("next_guidance") or disp_obj.get("next_action") or "").strip()
                    if nxt_content:
                        parsed_sections.append(AnswerSection(
                            type="next_action",
                            title="Next Step" if detected_language == "en" else "पुढील पाऊल" if detected_language == "mr" else "अगला कदम",
                            content=nxt_content,
                        ))

            # If direct_answer is still empty, synthesize from parsed sections
            if not direct_answer:
                if parsed_sections and parsed_sections[0].items and parsed_sections[0].items[0].title:
                    direct_answer = parsed_sections[0].items[0].title
                elif parsed_sections and parsed_sections[0].content:
                    direct_answer = parsed_sections[0].content
                elif json_payload.get("spoken_answer"):
                    direct_answer = json_payload["spoken_answer"]
                else:
                    direct_answer = "सहाय्यता तपशील खालीलप्रमाणे आहेत:" if detected_language == "mr" else "सहायता विवरण निम्नलिखित है:" if detected_language == "hi" else "Here is the guidance:"

            # 3. Spoken Answer
            llm_spoken = json_payload.get("spoken_answer") or disp_obj.get("spoken_answer") or ""
            if llm_spoken and len(llm_spoken.strip()) > 5:
                spoken_answer = clean_speech_text(llm_spoken)
            else:
                spoken_answer = clean_speech_text(direct_answer)

            # 4. Build Clean Structured Markdown for display_answer fallback
            md_blocks = []
            if direct_answer:
                md_blocks.append(direct_answer)

            for sec in parsed_sections:
                if sec.title:
                    md_blocks.append(f"### {sec.title}")
                if sec.type == "key_facts" and sec.items:
                    fact_lines = []
                    for itm in sec.items:
                        if itm.label and itm.value:
                            fact_lines.append(f"- **{itm.label}:** {itm.value}")
                        elif itm.label or itm.value:
                            fact_lines.append(f"- {itm.label or itm.value}")
                    if fact_lines:
                        md_blocks.append("\n".join(fact_lines))
                elif sec.type == "steps" and sec.items:
                    step_lines = []
                    for idx, itm in enumerate(sec.items, 1):
                        t = itm.title or f"Step {idx}"
                        d = itm.description or ""
                        if d:
                            step_lines.append(f"{idx}. **{t}:** {d}")
                        else:
                            step_lines.append(f"{idx}. {t}")
                    if step_lines:
                        md_blocks.append("\n".join(step_lines))
                elif sec.type in {"documents", "where_to_go"} and sec.items:
                    doc_lines = []
                    for itm in sec.items:
                        n = itm.name or itm.title or ""
                        d = itm.description or itm.content or ""
                        if n and d:
                            doc_lines.append(f"- **{n}:** {d}")
                        elif n:
                            doc_lines.append(f"- {n}")
                    if doc_lines:
                        md_blocks.append("\n".join(doc_lines))
                elif sec.content:
                    md_blocks.append(sec.content)

            parsed_display = "\n\n".join(md_blocks).strip()

            sanitized_answer, claims_valid, corrected_claims = validate_and_sanitize_claims(
                raw_answer=parsed_display,
                language=detected_language,
                intent=intent,
                grounding_context=combined_context,
            )

            display_answer = sanitized_answer.strip()

            structured_payload = StructuredAnswerPayload(
                direct_answer=direct_answer,
                sections=parsed_sections,
                spoken_answer=spoken_answer,
                suggested_followups=[],
            )
        else:
            settings = get_settings()
            provider_name = (settings.ai_provider or "ollama").lower().strip()
            if provider_name == "ollama":
                logger.warning("Local Ollama provider failed or is unavailable. Returning structured unavailable error.")
                display_answer = LOCAL_UNAVAILABLE_MESSAGE
            else:
                logger.warning("Primary provider failed. Using neutral error fallback.")
                raw_fallback = get_intent_fallback(intent, detected_language, answer_focus)
                display_answer = raw_fallback.strip()

            spoken_answer = clean_speech_text(display_answer)

            # SOURCE DISSOCIATION: Disassociate retrieved sources on technical generation failure
            sources_list = []
            primary_source = None
            claims_valid = False

            structured_payload = StructuredAnswerPayload(
                direct_answer=display_answer,
                sections=[],
                spoken_answer=spoken_answer,
                suggested_followups=[],
            )

        g_status, overall_auth_level, claims_validated = evaluate_grounding_status(
            sources_list=sources_list,
            claims_valid=claims_valid,
        )

        # Stage 9: Update Session State Post-Turn
        session.pending_slot = detect_pending_slot_from_answer(display_answer)
        session.last_assistant_question = display_answer
        session.history.append({"role": "user", "content": message})
        session.history.append({"role": "assistant", "content": display_answer})

        total_latency_ms = (time.perf_counter() - request_start) * 1000.0

        rag_executed = bool(rag_chunks)
        web_executed = bool(web_results)
        test_passed = (g_status in {"VERIFIED", "PARTIALLY_VERIFIED"})

        if router_mode == RouterMode.CURRENT_INFORMATION and not (web_executed or rag_executed):
            test_passed = False

        # Log Strict Telemetry Format
        logger.info(
            f"\n[FULL TELEMETRY]\n"
            f"SESSION_ID={session_id}\n"
            f"TURN_NUMBER={session.turn_number}\n"
            f"QUERY='{message}'\n"
            f"DETECTED_LANGUAGE={detected_language}\n"
            f"RESPONSE_LANGUAGE={response_language}\n"
            f"INTENT={intent}\n"
            f"TOPIC={current_topic}\n"
            f"USER_GOAL={current_goal}\n"
            f"PENDING_SLOT_BEFORE={pending_slot_before}\n"
            f"EXTRACTED_SLOT={extracted_slot}\n"
            f"PENDING_SLOT_AFTER={session.pending_slot}\n"
            f"CONTEXT_USED={context_used}\n"
            f"CONTEXT_FIELDS={session.collected_slots}\n"
            f"ROUTER={router_mode.value}\n"
            f"RAG_USED={rag_executed}\n"
            f"RAG_SOURCES={rag_source_titles}\n"
            f"WEB_SEARCH_USED={web_executed}\n"
            f"TRUSTED_SOURCES={web_source_urls}\n"
            f"SEARCH_QUERY='{effective_search_query}'\n"
            f"GROUNDING_STATUS={g_status}\n"
            f"SOURCE_AUTHORITY={overall_auth_level}\n"
            f"CLAIMS_VALIDATED={claims_validated}\n"
            f"RESPONSE_MODE={resp_mode}\n"
            f"LLM_ACTUALLY_CALLED=True\n"
            f"LLM={used_model}\n"
            f"SPOKEN_LANGUAGE={spoken_answer[:60]}...\n"
            f"TTS_LANGUAGE={tts_language}\n"
            f"FOLLOW_UP_LISTENING=True\n"
            f"TOTAL_LATENCY_MS={total_latency_ms:.2f}ms\n"
            f"RESULT={'PASSED' if test_passed else 'FAILED'}"
        )

        # Generate / Validate contextual suggested follow-up questions
        raw_followups = json_payload.get("suggested_followups") if json_payload and isinstance(json_payload, dict) else None
        followup_dicts = generate_contextual_followups(
            intent=intent,
            topic=current_topic,
            answer_focus=answer_focus,
            language=detected_language,
            message=message,
            llm_followups=raw_followups,
        )

        followup_models = [
            SuggestedFollowup(label=f["label"], query=f["query"])
            for f in followup_dicts
        ]

        if structured_payload:
            structured_payload.suggested_followups = followup_models

        response_obj = QueryResponse(
            answer=display_answer,
            structured_answer=structured_payload,
            display_answer=display_answer,
            spoken_answer=spoken_answer,
            language=response_language,
            intent=intent,
            answer_focus=answer_focus,
            source=primary_source,
            sources=sources_list,
            suggested_followups=followup_models,
            next_action="Follow up or ask another cooperative query",
            session_id=session_id,
            grounding_status=g_status,
            authority_level=overall_auth_level,
            claims_validated=claims_validated,
        )

        return response_obj, sources_list
