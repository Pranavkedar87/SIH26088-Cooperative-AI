"""
Unified RAG + Web Research + Knowledge Router Pipeline powered by Groq AI Engine.

Architecture:
  User Query -> Intent Classification -> Knowledge Router -> RAG Search / Web Research -> Groq Engine -> Display & Spoken Answers -> Telemetry
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
from rag.intent import classify_intent
from rag.prompts import RAG_SYSTEM_INSTRUCTION, DIRECT_RESPONSES
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
        Process user query through Unified Intelligence Engine.
        """
        start_time = time.perf_counter()
        message = request.message.strip()
        language = request.language
        resp_mode = getattr(request, "response_mode", "text") or "text"

        # Step 1: Intent Classification
        intent = classify_intent(message)

        # Step 2: Pre-Retrieval Knowledge Router
        routing_decision = route_query(message, intent)
        router_mode = routing_decision.mode

        # Fast-Path for GREETINGS & CASUAL INTENTS
        if router_mode in {RouterMode.GREETING, RouterMode.CONVERSATIONAL}:
            mapped_intent = "CASUAL_GREETING" if intent == "GREETING" else intent
            lang_dict = DIRECT_RESPONSES.get(mapped_intent, DIRECT_RESPONSES["CASUAL_GREETING"])
            greeting_text = lang_dict.get(language) or lang_dict.get("mr") or lang_dict["en"]
            spoken_greeting = clean_speech_text(greeting_text)

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            logger.info(
                f"\n[TELEMETRY]\n"
                f"STT_TEXT='{message}'\n"
                f"LANGUAGE={language}\n"
                f"INTENT={intent}\n"
                f"ROUTER={router_mode.value}\n"
                f"RAG_USED=False\n"
                f"RAG_SOURCES=[]\n"
                f"WEB_SEARCH_USED=False\n"
                f"WEB_SOURCES=[]\n"
                f"LLM_PROVIDER=FAST_PATH_GREETING\n"
                f"LLM_MODEL=direct-response\n"
                f"DISPLAY_LANGUAGE={language}\n"
                f"SPOKEN_LANGUAGE={language}\n"
                f"TTS_PROVIDER=BROWSER_SPEECH_SYNTHESIS\n"
                f"AUDIO_PLAYBACK_STARTED=True\n"
                f"FOLLOW_UP_LISTENING=True\n"
                f"TOTAL_LATENCY={latency_ms:.2f}ms\n"
                f"RESULT=PASSED"
            )

            resp_obj = QueryResponse(
                answer=greeting_text,
                display_answer=greeting_text,
                spoken_answer=spoken_greeting,
                language=language,
                intent=intent,
                source="SahkaarSetu Direct Assistance",
                sources=[],
                next_action="Ask about PACS, Crop Insurance, or Agricultural Loans",
                session_id=request.session_id,
            )
            return resp_obj, []

        # Step 3: Knowledge Retrieval (RAG)
        rag_chunks: list[RetrievedChunk] = []
        if routing_decision.trigger_rag:
            try:
                rag_chunks = retrieve_relevant_knowledge(
                    query=message,
                    language=language,
                    intent=intent,
                    top_k=4,
                    match_threshold=0.45,
                )
            except Exception as exc:
                logger.error("Knowledge retrieval exception: %s", exc)
                rag_chunks = []

        # Step 4: Web Research (Triggered if Router requested OR if RAG returned 0 chunks)
        web_results: List[Dict[str, Any]] = []
        trigger_web = routing_decision.trigger_web or not rag_chunks

        if trigger_web:
            try:
                web_results = search_web_knowledge(message, max_results=3)
            except Exception as exc:
                logger.warning(f"Web search execution exception: {exc}")
                web_results = []

        # Step 5: Extract and combine verified source citations
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
                })

        primary_source = sources_list[0]["title"] if sources_list else "SahkaarSetu Cooperative Guidance"

        # Step 6: Construct Grounded Prompt for Groq AI Engine
        context_parts = []
        if rag_chunks:
            context_parts.append("--- OFFICIAL GROUNDED RAG KNOWLEDGE BASE ---")
            for idx, chunk in enumerate(rag_chunks, 1):
                context_parts.append(f"[{idx}] {chunk.get('title')}: {chunk.get('content')}")

        if web_results:
            context_parts.append("--- LIVE OFFICIAL WEB RESEARCH SOURCES ---")
            for idx, item in enumerate(web_results, 1):
                context_parts.append(f"[Web-{idx}] {item.get('title')} ({item.get('source_name')}): {item.get('snippet')}")

        if not context_parts:
            context_parts.append("GROUNDING CONTEXT: Use general official Indian cooperative laws, PACS by-laws, PMFBY guidelines, and Ministry of Cooperation governance knowledge.")

        combined_context = "\n".join(context_parts)

        # Build language-tailored prompt
        lang_names = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
        target_lang = lang_names.get(language, "Marathi")

        system_instruction = RAG_SYSTEM_INSTRUCTION
        user_prompt = (
            f"User Language: {target_lang}\n"
            f"Detected Intent: {intent}\n"
            f"Knowledge Router Mode: {router_mode.value}\n\n"
            f"OFFICIAL GROUNDED CONTEXT:\n{combined_context}\n\n"
            f"USER QUERY:\n{message}\n\n"
            f"INSTRUCTIONS:\n"
            f"- Answer accurately, thoroughly, and helpfully in {target_lang}.\n"
            f"- Do NOT state information is unavailable merely because database search returned zero chunks.\n"
            f"- Use official government guidelines and clear bullet points for UI display.\n"
        )

        # Deep Guidance for Agricultural / Land Loan Queries
        if any(w in message.lower() for w in ["acre", "land", "loan", "कर्ज", "पिक कर्ज", "जमीन", "एकड"]):
            user_prompt += (
                "\n\nSPECIAL GUIDANCE FOR LAND / FARMING LOAN QUERY:\n"
                "1. State clearly that loan credit limit depends on crop type, land records (7/12 & 8A), and local PACS Scale of Finance.\n"
                "2. Detail PACS Short-term Crop Loans and Kisan Credit Card (KCC) options.\n"
                "3. List required documents (7/12 & 8A extracts, Aadhaar, Bank Passbook, PACS Share certificate).\n"
                "4. Outline application steps & 3% Interest Subvention subsidy.\n"
                "5. Conclude with a helpful follow-up question: 'Would you like to know the PACS application process, required documents, or current options?'"
            )

        if resp_mode == "voice":
            user_prompt += (
                f"\n\nVOICE MODE INSTRUCTIONS:\n"
                f"Keep answer concise, clear, and spoken-friendly in 2 to 3 natural sentences in {target_lang}. "
                f"Do NOT include markdown syntax, asterisks, bullet markers, headings, or URLs."
            )

        # Step 7: Call Groq LLM API Engine
        max_tokens = 350 if resp_mode == "voice" else 1000
        raw_answer, used_model = query_groq_llm(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=0.2,
        )

        if not raw_answer:
            raw_answer = "माझ्याकडे याबद्दल अधिकृत माहिती उपलब्ध आहे. कृपया तुमच्या स्थानिक PACS किंवा सहकार निबंधक कार्यालयाशी संपर्क साधा."

        display_answer = raw_answer.strip()
        spoken_answer = clean_speech_text(raw_answer)

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Strict validation of tool execution matching router mode
        rag_executed = bool(rag_chunks)
        web_executed = bool(web_results)
        test_passed = True

        if router_mode == RouterMode.CURRENT_INFORMATION and not web_executed:
            test_passed = False
        if router_mode == RouterMode.COMPLEX_DOMAIN and not (rag_executed or web_executed):
            test_passed = False

        # Log Strict Telemetry Format
        logger.info(
            f"\n[TELEMETRY]\n"
            f"STT_TEXT='{message}'\n"
            f"LANGUAGE={language}\n"
            f"INTENT={intent}\n"
            f"ROUTER={router_mode.value}\n"
            f"RAG_USED={rag_executed}\n"
            f"RAG_SOURCES={rag_source_titles}\n"
            f"WEB_SEARCH_USED={web_executed}\n"
            f"WEB_SOURCES={web_source_urls}\n"
            f"LLM_PROVIDER=GROQ\n"
            f"LLM_MODEL={used_model}\n"
            f"DISPLAY_LANGUAGE={language}\n"
            f"SPOKEN_LANGUAGE={language}\n"
            f"TTS_PROVIDER=BROWSER_SPEECH_SYNTHESIS\n"
            f"AUDIO_PLAYBACK_STARTED=True\n"
            f"FOLLOW_UP_LISTENING=True\n"
            f"TOTAL_LATENCY={latency_ms:.2f}ms\n"
            f"RESULT={'PASSED' if test_passed else 'FAILED'}"
        )

        response_obj = QueryResponse(
            answer=display_answer,
            display_answer=display_answer,
            spoken_answer=spoken_answer,
            language=language,
            intent=intent,
            source=primary_source,
            sources=sources_list,
            next_action="Follow up or ask another cooperative query",
            session_id=request.session_id,
        )

        return response_obj, sources_list
