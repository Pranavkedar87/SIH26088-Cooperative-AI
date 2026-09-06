"""
Unified RAG + Web Research + Knowledge Router Pipeline powered by Groq AI Engine.

Architecture:
  User Query -> Session State Resolution -> Intent Classification & Topic Extraction -> Knowledge Router -> RAG Search / Web Research -> Groq Engine -> Display & Spoken Answers -> Telemetry
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any, Optional, Dict, List

from app.config import get_settings
from app.providers.groq_provider import query_groq_llm, GROQ_MODELS
from app.schemas.query import IntentCode, QueryRequest, QueryResponse
from rag.intent import classify_intent, extract_topic_and_goal
from rag.prompts import RAG_SYSTEM_INSTRUCTION, DIRECT_RESPONSES, NO_KNOWLEDGE_FALLBACK, NO_KNOWLEDGE_FALLBACK_WITH_STATE
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
    Strips markdown formatting, headings, bullet markers, URLs, citations, and '::' artifacts
    for clean natural speech TTS audio playback.
    """
    if not text:
        return ""
    # Strip URLs
    cleaned = re.sub(r'https?://\S+', '', text)
    # Strip markdown headers, asterisks, underscores, backticks, hashes, bullet symbols
    cleaned = re.sub(r'#+\s*', '', cleaned)
    cleaned = re.sub(r'[\*\_\`]', '', cleaned)
    # Strip :: artifacts or technical metadata
    cleaned = re.sub(r'::+', ' ', cleaned)
    # Strip citation brackets e.g. [1], [Web-1], [Source: ...]
    cleaned = re.sub(r'\[\s*(?:web-)?\d+\s*\]', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
    # Strip leading bullet numbers/markers line by line
    cleaned = re.sub(r'^\s*[-*+•]\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*\d+[\.\)]\s+', '', cleaned, flags=re.MULTILINE)
    # Collapse multiple whitespaces & newlines into clean natural speech spacing
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


class RAGPipeline:
    """Orchestrates end-to-end grounded query answering using Groq AI Engine with Multi-Turn Conversational State."""

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
        intent = classify_intent(message)
        extracted_topic, extracted_goal = extract_topic_and_goal(message)
        intent_latency_ms = (time.perf_counter() - intent_start) * 1000.0

        # Topic & Goal Persistence across turns
        if extracted_topic != "GENERAL_COOPERATIVE_QUERY":
            session.topic = extracted_topic
            session.user_goal = extracted_goal
        elif session.topic:
            context_used = True

        current_topic = session.topic or extracted_topic
        current_goal = session.user_goal or extracted_goal

        # Stage 3: Pre-Retrieval Knowledge Router
        router_start = time.perf_counter()
        routing_decision = route_query(message, intent)
        router_mode = routing_decision.mode
        router_latency_ms = (time.perf_counter() - router_start) * 1000.0

        # Fast-Path for GREETINGS & CASUAL INTENTS
        if router_mode in {RouterMode.GREETING, RouterMode.CONVERSATIONAL}:
            mapped_intent = "CASUAL_GREETING" if intent == "GREETING" else intent
            lang_dict = DIRECT_RESPONSES.get(mapped_intent, DIRECT_RESPONSES["CASUAL_GREETING"])
            greeting_text = lang_dict.get(detected_language) or lang_dict.get("en") or lang_dict["mr"]
            spoken_greeting = clean_speech_text(greeting_text)

            total_latency_ms = (time.perf_counter() - request_start) * 1000.0

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
                f"RAG_USED=False\n"
                f"WEB_SEARCH_USED=False\n"
                f"SEARCH_QUERY=''\n"
                f"SOURCES=[]\n"
                f"RESPONSE_MODE={resp_mode}\n"
                f"LLM_ACTUALLY_CALLED=False\n"
                f"LLM=None\n"
                f"SPOKEN_LANGUAGE={spoken_greeting[:50]}...\n"
                f"TTS_LANGUAGE={tts_language}\n"
                f"FOLLOW_UP_LISTENING=True\n"
                f"TOTAL_LATENCY_MS={total_latency_ms:.2f}ms\n"
                f"RESULT=PASSED"
            )

            resp_obj = QueryResponse(
                answer=greeting_text,
                display_answer=greeting_text,
                spoken_answer=spoken_greeting,
                language=response_language,
                intent=intent,
                source="SahkaarSetu Direct Assistance",
                sources=[],
                next_action="Ask about PACS, Crop Insurance, or Agricultural Loans",
                session_id=session_id,
            )
            return resp_obj, []

        # Stage 4: Knowledge Retrieval (RAG)
        rag_start = time.perf_counter()
        effective_search_query = message
        if session.collected_slots.get("state"):
            effective_search_query = f"{message} {current_topic} {session.collected_slots.get('state')} Maharashtra scheme"

        rag_chunks: list[RetrievedChunk] = []
        if routing_decision.trigger_rag:
            try:
                rag_chunks = retrieve_relevant_knowledge(
                    query=effective_search_query,
                    language=detected_language,
                    intent=intent,
                    top_k=4,
                    match_threshold=0.45,
                )
            except Exception as exc:
                logger.error("Knowledge retrieval exception: %s", exc)
                rag_chunks = []
        rag_latency_ms = (time.perf_counter() - rag_start) * 1000.0

        # Stage 5: Live Official Web Research
        web_start = time.perf_counter()
        web_results: List[Dict[str, Any]] = []
        trigger_web = routing_decision.trigger_web or not rag_chunks

        if trigger_web:
            try:
                web_results = search_web_knowledge(effective_search_query, max_results=3)
            except Exception as exc:
                logger.warning(f"Web search execution exception: {exc}")
                web_results = []
        web_search_latency_ms = (time.perf_counter() - web_start) * 1000.0

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

        # Filter out non-authoritative sources (e.g. Wikipedia) and enrich with authority levels and timestamps
        sources_list = sanitize_source_citations(sources_list, is_legal_or_gov_query=True)
        primary_source = sources_list[0]["title"] if sources_list else "SahkaarSetu Cooperative Guidance"

        # Stage 7: Construct Grounded Prompt for Groq AI Engine
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
            context_parts.append("GROUNDING CONTEXT: Use official Indian government agricultural mechanization guidelines, PACS rules, PMFBY policies, and Ministry of Cooperation schemes.")

        combined_context = "\n".join(context_parts)

        # Build language-tailored prompt
        lang_names = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
        target_lang = lang_names.get(detected_language, "English")

        system_instruction = RAG_SYSTEM_INSTRUCTION
        user_prompt = (
            f"STRICT RESPONSE LANGUAGE: {target_lang}\n"
            f"Active Session Turn: {session.turn_number}\n"
            f"Detected Intent: {intent}\n"
            f"Active Topic: {current_topic}\n"
            f"Active User Goal: {current_goal}\n"
            f"Collected Session Slots: {session.collected_slots}\n"
            f"Pending Slot Before Turn: {pending_slot_before}\n"
            f"Knowledge Router Mode: {router_mode.value}\n\n"
            f"OFFICIAL GROUNDED CONTEXT:\n{combined_context}\n\n"
            f"USER QUERY:\n{message}\n\n"
            f"STRICT INSTRUCTIONS:\n"
            f"- Answer ONLY and COMPLETELY in {target_lang}.\n"
        )

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
                f"Keep answer concise, clear, and spoken-friendly in 2 to 3 natural sentences in {target_lang}. "
                f"Do NOT include markdown syntax, asterisks, bullet markers, headings, or URLs."
            )

        prompt_build_latency_ms = (time.perf_counter() - prompt_start) * 1000.0

        # Stage 8: Call Groq LLM API Engine
        max_tokens = 250 if resp_mode == "voice" else 450
        raw_answer, used_model, llm_stats = query_groq_llm(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=0.2,
        )

        if not raw_answer:
            if session.collected_slots.get("state"):
                raw_answer = NO_KNOWLEDGE_FALLBACK_WITH_STATE.get(detected_language, NO_KNOWLEDGE_FALLBACK_WITH_STATE["en"])
            else:
                raw_answer = NO_KNOWLEDGE_FALLBACK.get(detected_language, NO_KNOWLEDGE_FALLBACK["en"])

        # Stage 8.5: Factual Claim Grounding & Source Validation Stage
        sanitized_answer, claims_valid, corrected_claims = validate_and_sanitize_claims(
            raw_answer=raw_answer,
            language=detected_language,
            intent=intent,
            grounding_context=combined_context,
        )

        g_status, overall_auth_level, claims_validated = evaluate_grounding_status(
            sources_list=sources_list,
            claims_valid=claims_valid,
        )

        display_answer = sanitized_answer.strip()
        spoken_answer = clean_speech_text(sanitized_answer)

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
            f"LLM=GROQ ({used_model})\n"
            f"SPOKEN_LANGUAGE={spoken_answer[:60]}...\n"
            f"TTS_LANGUAGE={tts_language}\n"
            f"FOLLOW_UP_LISTENING=True\n"
            f"TOTAL_LATENCY_MS={total_latency_ms:.2f}ms\n"
            f"RESULT={'PASSED' if test_passed else 'FAILED'}"
        )

        response_obj = QueryResponse(
            answer=display_answer,
            display_answer=display_answer,
            spoken_answer=spoken_answer,
            language=response_language,
            intent=intent,
            source=primary_source,
            sources=sources_list,
            next_action="Follow up or ask another cooperative query",
            session_id=session_id,
            grounding_status=g_status,
            authority_level=overall_auth_level,
            claims_validated=claims_validated,
        )

        return response_obj, sources_list
