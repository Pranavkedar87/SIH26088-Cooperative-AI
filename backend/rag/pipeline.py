"""
Unified RAG + Web Research + Knowledge Router Pipeline powered by Groq AI Engine.

Architecture:
  User Query -> Intent Classification & Topic Extraction -> Knowledge Router -> RAG Search / Web Research -> Groq Engine -> Display & Spoken Answers -> Telemetry
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
from rag.prompts import RAG_SYSTEM_INSTRUCTION, DIRECT_RESPONSES, NO_KNOWLEDGE_FALLBACK
from rag.retriever import retrieve_relevant_knowledge, RetrievedChunk
from rag.router import route_query, RouterMode, RoutingDecision
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
    """Orchestrates end-to-end grounded query answering using Groq AI Engine."""

    async def process_query(self, request: QueryRequest) -> tuple[QueryResponse, list[dict[str, Any]]]:
        """
        Process user query through Unified Intelligence Engine with strict language propagation.
        """
        request_start = time.perf_counter()
        message = request.message.strip()
        detected_language = request.language or "en"
        response_language = detected_language
        tts_language = detected_language
        resp_mode = getattr(request, "response_mode", "text") or "text"

        # Stage 1: Intent Classification & Topic/Goal Extraction
        intent_start = time.perf_counter()
        intent = classify_intent(message)
        topic, user_goal = extract_topic_and_goal(message)
        intent_latency_ms = (time.perf_counter() - intent_start) * 1000.0

        # Stage 2: Pre-Retrieval Knowledge Router
        router_start = time.perf_counter()
        routing_decision = route_query(message, intent)
        router_mode = routing_decision.mode
        router_latency_ms = (time.perf_counter() - router_start) * 1000.0

        # Fast-Path for GREETINGS & CASUAL INTENTS (Strict language response)
        if router_mode in {RouterMode.GREETING, RouterMode.CONVERSATIONAL}:
            mapped_intent = "CASUAL_GREETING" if intent == "GREETING" else intent
            lang_dict = DIRECT_RESPONSES.get(mapped_intent, DIRECT_RESPONSES["CASUAL_GREETING"])
            greeting_text = lang_dict.get(detected_language) or lang_dict.get("en") or lang_dict["mr"]
            spoken_greeting = clean_speech_text(greeting_text)

            total_latency_ms = (time.perf_counter() - request_start) * 1000.0

            logger.info(
                f"\n[FULL TELEMETRY]\n"
                f"QUERY='{message}'\n"
                f"DETECTED_LANGUAGE={detected_language}\n"
                f"RESPONSE_LANGUAGE={response_language}\n"
                f"INTENT={intent}\n"
                f"TOPIC={topic}\n"
                f"USER_GOAL={user_goal}\n"
                f"ROUTER={router_mode.value}\n"
                f"RAG_USED=False\n"
                f"RAG_SOURCES=[]\n"
                f"WEB_SEARCH_USED=False\n"
                f"TRUSTED_SOURCES=[]\n"
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
                session_id=request.session_id,
            )
            return resp_obj, []

        # Stage 3: Knowledge Retrieval (RAG)
        rag_start = time.perf_counter()
        rag_chunks: list[RetrievedChunk] = []
        if routing_decision.trigger_rag:
            try:
                rag_chunks = retrieve_relevant_knowledge(
                    query=message,
                    language=detected_language,
                    intent=intent,
                    top_k=4,
                    match_threshold=0.45,
                )
            except Exception as exc:
                logger.error("Knowledge retrieval exception: %s", exc)
                rag_chunks = []
        rag_latency_ms = (time.perf_counter() - rag_start) * 1000.0

        # Stage 4: Live Official Web Research
        web_start = time.perf_counter()
        web_results: List[Dict[str, Any]] = []
        trigger_web = routing_decision.trigger_web or not rag_chunks

        if trigger_web:
            try:
                web_results = search_web_knowledge(message, max_results=3)
            except Exception as exc:
                logger.warning(f"Web search execution exception: {exc}")
                web_results = []
        web_search_latency_ms = (time.perf_counter() - web_start) * 1000.0

        # Stage 5: Extract and combine verified source citations with Authority Levels
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

        primary_source = sources_list[0]["title"] if sources_list else "SahkaarSetu Cooperative Guidance"

        # Stage 6: Construct Grounded Prompt for Groq AI Engine
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

        # Build language-tailored prompt (STRICT LANGUAGE ENFORCEMENT)
        lang_names = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
        target_lang = lang_names.get(detected_language, "English")

        system_instruction = RAG_SYSTEM_INSTRUCTION
        user_prompt = (
            f"STRICT RESPONSE LANGUAGE: {target_lang}\n"
            f"Detected Intent: {intent}\n"
            f"Extracted Topic: {topic}\n"
            f"User Practical Goal: {user_goal}\n"
            f"Knowledge Router Mode: {router_mode.value}\n\n"
            f"OFFICIAL GROUNDED CONTEXT:\n{combined_context}\n\n"
            f"USER QUERY:\n{message}\n\n"
            f"STRICT LANGUAGE INSTRUCTION: Answer ONLY and COMPLETELY in {target_lang}. Do NOT use any other language.\n"
        )

        # Specific guidance for Tractor / Farm Machinery queries
        if topic == "TRACTOR_PURCHASE":
            if detected_language == "en":
                user_prompt += (
                    "\n\nSPECIAL TRACTOR SCHEME INSTRUCTIONS:\n"
                    "1. Explain clearly that government assistance/subsidy for purchasing tractors and farm machinery is available under schemes like Sub-Mission on Agricultural Mechanization (SMAM) and State Agriculture Departments.\n"
                    "2. State that eligibility and subsidy percentages depend on your state and farmer category.\n"
                    "3. Conclude with a helpful follow-up question: 'Which state are you from? I can check the official scheme and subsidy details for your state.'"
                )
            elif detected_language == "hi":
                user_prompt += (
                    "\n\nSPECIAL TRACTOR SCHEME INSTRUCTIONS:\n"
                    "1. स्पष्ट बताएं कि ट्रैक्टर और कृषि उपकरण खरीदने के लिए 'कृषि मशीनीकरण पर उप-मिशन' (SMAM) और राज्य कृषि विभागों के तहत सब्सिडी/सहायता उपलब्ध है।\n"
                    "2. बताएं कि पात्रता और सब्सिडी की राशि राज्य और किसान श्रेणी पर निर्भर करती है।\n"
                    "3. उपयोगी प्रश्न के साथ समाप्त करें: 'आप किस राज्य से हैं? मैं आपके राज्य के लिए आधिकारिक योजना की जानकारी देख सकता हूँ।'"
                )
            elif detected_language == "mr":
                user_prompt += (
                    "\n\nSPECIAL TRACTOR SCHEME INSTRUCTIONS:\n"
                    "1. ट्रॅक्टर आणि कृषी अवजारे खरेदीसाठी 'कृषी यांत्रिकीकरण उप-अभियान' (SMAM) आणि राज्य कृषी विभागाच्या योजनांतर्गत अनुदान उपलब्ध असल्याचे स्पष्ट सांगा.\n"
                    "2. अनुदान व पात्रता ही तुमच्या राज्यावर आणि शेतकरी वर्गावर अवलंबून असल्याचे सांगा.\n"
                    "3. शेवटी विचारा: 'तुम्ही कोणत्या राज्यातील आहात? मी तुमच्या राज्यासाठी अधिकृत योजना तपासू शकतो.'"
                )

        if resp_mode == "voice":
            user_prompt += (
                f"\n\nVOICE MODE INSTRUCTIONS:\n"
                f"Keep answer concise, clear, and spoken-friendly in 2 to 3 natural sentences in {target_lang}. "
                f"Do NOT include markdown syntax, asterisks, bullet markers, headings, or URLs."
            )

        prompt_build_latency_ms = (time.perf_counter() - prompt_start) * 1000.0

        # Stage 7: Call Groq LLM API Engine
        max_tokens = 250 if resp_mode == "voice" else 450
        raw_answer, used_model, llm_stats = query_groq_llm(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=0.2,
        )

        if not raw_answer:
            raw_answer = NO_KNOWLEDGE_FALLBACK.get(detected_language, NO_KNOWLEDGE_FALLBACK["en"])

        display_answer = raw_answer.strip()
        spoken_answer = clean_speech_text(raw_answer)

        total_latency_ms = (time.perf_counter() - request_start) * 1000.0

        # Strict validation of tool execution matching router mode
        rag_executed = bool(rag_chunks)
        web_executed = bool(web_results)
        test_passed = True

        if router_mode == RouterMode.CURRENT_INFORMATION and not (web_executed or rag_executed):
            test_passed = False

        # Log Strict Telemetry Format
        logger.info(
            f"\n[FULL TELEMETRY]\n"
            f"QUERY='{message}'\n"
            f"DETECTED_LANGUAGE={detected_language}\n"
            f"RESPONSE_LANGUAGE={response_language}\n"
            f"INTENT={intent}\n"
            f"TOPIC={topic}\n"
            f"USER_GOAL={user_goal}\n"
            f"ROUTER={router_mode.value}\n"
            f"RAG_USED={rag_executed}\n"
            f"RAG_SOURCES={rag_source_titles}\n"
            f"WEB_SEARCH_USED={web_executed}\n"
            f"TRUSTED_SOURCES={web_source_urls}\n"
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
            session_id=request.session_id,
        )

        return response_obj, sources_list
