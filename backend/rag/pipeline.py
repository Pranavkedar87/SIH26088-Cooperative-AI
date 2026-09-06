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
    """Extracts and parses structured JSON object from LLM response text."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    return None

from app.config import get_settings
from app.providers.groq_provider import query_groq_llm, GROQ_MODELS
from app.providers.gemini_provider import query_gemini_llm
from app.schemas.query import IntentCode, QueryRequest, QueryResponse
from rag.intent import classify_intent, extract_topic_and_goal
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


def generate_structured_answer(
    system_instruction: str,
    user_prompt: str,
    max_tokens: int = 850,
) -> tuple[Optional[dict[str, Any]], str, dict[str, Any]]:
    """
    Provider-agnostic generator that attempts to produce a canonical structured JSON answer.
    Fallback Chain:
      1. Gemini Primary (gemini-2.5-flash) with response_mime_type="application/json"
      2. Groq Primary (llama-3.3-70b-versatile) with response_format={"type": "json_object"}
      3. Groq Fallback (llama-3.1-8b-instant) with response_format={"type": "json_object"}
    """
    # 1. Gemini Primary
    raw_answer, used_model, gemini_stats = query_gemini_llm(
        system_instruction=system_instruction,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        temperature=0.2,
        response_mime_type="application/json",
    )
    if raw_answer:
        payload = extract_json_payload(raw_answer)
        if payload and isinstance(payload, dict) and ("display_answer" in payload or "summary" in payload or "title" in payload):
            logger.info(f"[PROVIDER-AGNOSTIC LLM] Structured output generated via Gemini ({used_model})")
            return payload, f"GEMINI ({used_model})", gemini_stats

    # 2 & 3. Groq Fallback Chain
    logger.info("[PROVIDER-AGNOSTIC LLM] Gemini primary unavailable or returned non-JSON. Trying Groq fallback chain...")
    raw_answer, used_model, groq_stats = query_groq_llm(
        system_instruction=system_instruction,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    if raw_answer:
        payload = extract_json_payload(raw_answer)
        if payload and isinstance(payload, dict) and ("display_answer" in payload or "summary" in payload or "title" in payload):
            logger.info(f"[PROVIDER-AGNOSTIC LLM] Structured output generated via Groq ({used_model})")
            return payload, f"GROQ ({used_model})", groq_stats

    return None, "none", {}


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



        # Stage 4: AI Search Query Generation & Knowledge Retrieval (RAG)
        rag_start = time.perf_counter()
        is_followup = (
            len(message.split()) <= 6 and 
            session.topic and 
            session.topic != "GENERAL_COOPERATIVE_QUERY" and 
            len(session.history) > 0
        )

        if is_followup:
            effective_search_query = f"{session.topic} {message}"
        else:
            effective_search_query = message

        if session.collected_slots.get("state"):
            effective_search_query += f" {session.collected_slots.get('state')}"

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

        # Stage 5: Live Internet Web Research
        web_start = time.perf_counter()
        web_results: List[Dict[str, Any]] = []
        if routing_decision.trigger_web or (router_mode not in {RouterMode.GREETING, RouterMode.CONVERSATIONAL}):
            try:
                web_results = search_web_knowledge(effective_search_query, max_results=4)
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
            context_parts.append("GROUNDING CONTEXT: Use official Indian government agricultural mechanization guidelines, PACS rules, PMFBY policies, and Ministry of Cooperation schemes.")

        combined_context = "\n".join(context_parts)

        lang_names = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
        target_lang = lang_names.get(detected_language, "English")

        system_instruction = RAG_SYSTEM_INSTRUCTION
        user_prompt = (
            f"ORIGINAL USER QUESTION: {message}\n"
            f"STRICT RESPONSE LANGUAGE: {target_lang}\n"
            f"Detected Intent: {intent}\n"
            f"Active Session Turn: {session.turn_number}\n"
        )

        if session.history:
            history_lines = [f"{h['role'].upper()}: {h['content']}" for h in session.history[-4:]]
            user_prompt += f"\nPREVIOUS CONVERSATION HISTORY:\n" + "\n".join(history_lines) + "\n"

        user_prompt += (
            f"\nOFFICIAL GROUNDED CONTEXT:\n{combined_context}\n\n"
            f"STRICT INSTRUCTION: Synthesize the grounded context to answer the user's EXACT ORIGINAL QUESTION ('{message}') in {target_lang}. "
            f"Generate dynamic, question-specific action steps under 'what_should_i_do_now' and a direct spoken answer."
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

        # Stage 8: Call Provider-Agnostic LLM Engine (Gemini Primary -> Groq Fallback)
        max_tokens = 350 if resp_mode == "voice" else 850
        json_payload, used_model, llm_stats = generate_structured_answer(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )

        # Stage 8.5: Canonical Response Ingestion & Grounding Validation Stage
        if json_payload and isinstance(json_payload, dict):
            disp_obj = json_payload.get("display_answer") if isinstance(json_payload.get("display_answer"), dict) else json_payload

            title = disp_obj.get("title") or ""
            summary = disp_obj.get("summary") or ""
            actions = disp_obj.get("what_should_i_do_now") or []
            details = disp_obj.get("detailed_information") or ""
            next_guidance = disp_obj.get("next_guidance") or ""
            llm_spoken = json_payload.get("spoken_answer") or disp_obj.get("spoken_answer") or ""

            md_blocks = []
            if title:
                md_blocks.append(f"### {title}")
            if summary:
                md_blocks.append(summary)

            if actions and isinstance(actions, list):
                action_header = "What Should I Do Now:"
                if detected_language == "mr":
                    action_header = "तुम्ही काय करू शकता:"
                elif detected_language == "hi":
                    action_header = "आप क्या करें:"
                act_lines = [f"**{action_header}**"]
                for idx, act in enumerate(actions, 1):
                    if isinstance(act, dict):
                        act_title = act.get("title", f"Step {idx}")
                        act_content = act.get("content", "")
                        act_lines.append(f"{idx}. {act_title}: {act_content}")
                    elif isinstance(act, str) and act.strip():
                        act_str = act.strip()
                        if not re.match(r'^\d+\.', act_str):
                            act_lines.append(f"{idx}. {act_str}")
                        else:
                            act_lines.append(act_str)
                if len(act_lines) > 1:
                    md_blocks.append("\n".join(act_lines))

            if details:
                det_header = "Detailed Information:"
                if detected_language == "mr":
                    det_header = "सविस्तर माहिती:"
                elif detected_language == "hi":
                    det_header = "विस्तृत जानकारी:"
                md_blocks.append(f"**{det_header}**\n{details}")

            if next_guidance:
                guid_header = "Next Guidance:"
                if detected_language == "mr":
                    guid_header = "पुढील मार्गदर्शन:"
                elif detected_language == "hi":
                    guid_header = "आगे का मार्गदर्शन:"
                md_blocks.append(f"**{guid_header}**\n{next_guidance}")

            parsed_display = "\n\n".join(md_blocks).strip()

            sanitized_answer, claims_valid, corrected_claims = validate_and_sanitize_claims(
                raw_answer=parsed_display,
                language=detected_language,
                intent=intent,
                grounding_context=combined_context,
            )

            display_answer = sanitized_answer.strip()
            if llm_spoken and len(llm_spoken.strip()) > 5:
                spoken_answer = clean_speech_text(llm_spoken)
            else:
                spoken_answer = clean_speech_text(summary or display_answer)
        else:
            logger.warning("All LLM providers (Gemini & Groq) failed or returned invalid JSON. Using controlled source snippet fallback.")
            action_hdr = "What Should I Do Now:"
            if detected_language == "mr":
                action_hdr = "तुम्ही काय करू शकता:"
            elif detected_language == "hi":
                action_hdr = "आप क्या करें:"

            if web_results:
                top_snippets = [f"{idx}. {w.get('title')}: {w.get('snippet')}" for idx, w in enumerate(web_results[:3], 1)]
                raw_fallback = f"### Official Guidance\n\n**{action_hdr}**\n" + "\n".join(top_snippets)
            else:
                raw_fallback = f"### Official Guidance\n\n**{action_hdr}**\n1. Verify Details: {get_intent_fallback(intent, detected_language)}"

            sanitized_answer, claims_valid, corrected_claims = validate_and_sanitize_claims(
                raw_answer=raw_fallback,
                language=detected_language,
                intent=intent,
                grounding_context=combined_context,
            )
            display_answer = sanitized_answer.strip()
            spoken_answer = clean_speech_text(sanitized_answer)

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
