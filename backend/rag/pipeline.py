"""
RAG + Web Research Pipeline orchestrator powered by Groq.

Coordinates Intent Classification -> Knowledge Retrieval (RAG) / Live Web Search -> Grounded Groq Generation -> Structured Output.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Optional, Dict, List

from app.config import get_settings
from app.providers.gemini_provider import _classify_intent
from app.providers.groq_provider import query_groq_llm, GROQ_MODELS
from app.schemas.query import IntentCode, QueryRequest, QueryResponse
from rag.prompts import RAG_SYSTEM_INSTRUCTION, build_grounded_prompt, NO_KNOWLEDGE_FALLBACK, DIRECT_RESPONSES
from rag.retriever import retrieve_relevant_knowledge, RetrievedChunk
from rag.web_search import search_web_knowledge

logger = logging.getLogger(__name__)

# Intents requiring live web search for current/changing information
TIME_SENSITIVE_INTENTS: set[str] = {
    "MINISTRY_SCHEME",
    "PMFBY",
    "AGRICULTURAL_SUPPORT",
}

# Intents requiring strict RAG knowledge retrieval
STRICT_KNOWLEDGE_INTENTS: set[str] = {
    "COOPERATIVE_LAW",
    "COOPERATIVE_BYLAW",
    "MINISTRY_SCHEME",
    "PACS_SERVICE",
    "PMFBY",
    "AGRICULTURAL_SUPPORT",
    "FINANCIAL_LITERACY",
    "GRIEVANCE",
    "GENERAL_COOPERATIVE",
}


def clean_speech_text(text: str) -> str:
    """Strips markdown formatting, headings, bullet markers, URLs, and symbols for clean TTS playback."""
    if not text:
        return ""
    cleaned = re.sub(r'https?://\S+', '', text)
    cleaned = re.sub(r'#+\s*', '', cleaned)
    cleaned = re.sub(r'[\*\_\`]', '', cleaned)
    cleaned = re.sub(r'^\s*[-*+]\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*\d+\.\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


class RAGPipeline:
    """Orchestrates end-to-end grounded query answering using Groq AI Engine."""

    async def process_query(self, request: QueryRequest) -> tuple[QueryResponse, list[dict[str, Any]]]:
        """
        Process user query through RAG + Live Web Search + Groq Pipeline.
        """
        message = request.message.strip()
        language = request.language
        resp_mode = getattr(request, "response_mode", "text") or "text"

        # Step 1: Intent classification
        intent = _classify_intent(message)

        # FAST PATH FOR CASUAL GREETINGS, THANKS, IDENTITY & UNCLEAR:
        CASUAL_INTENTS = {"CASUAL_GREETING", "CASUAL_THANKS", "CASUAL_IDENTITY", "UNCLEAR", "GREETING"}
        if intent in CASUAL_INTENTS:
            mapped_intent = "CASUAL_GREETING" if intent == "GREETING" else intent
            lang_dict = DIRECT_RESPONSES.get(mapped_intent, DIRECT_RESPONSES["CASUAL_GREETING"])
            ans_text = lang_dict.get(language) or lang_dict.get("mr") or lang_dict["en"]

            logger.info(
                "\n========================================================\n"
                "[AI PROVIDER] GROQ (Fast-Path Greeting)\n"
                f"[MODEL] Direct Localized Response (<10ms)\n"
                f"[STT PROVIDER] WEB_SPEECH_API\n"
                f"[TTS PROVIDER] BROWSER_SPEECH_SYNTHESIS\n"
                f"[QUERY] '{message}'\n"
                f"[INTENT] {intent}\n"
                f"[RAG TRIGGERED] false\n"
                f"[WEB SEARCH TRIGGERED] false\n"
                "========================================================"
            )

            return QueryResponse(
                answer=ans_text,
                language=language,
                intent=intent,
                source="SahkaarSetu Direct Assistance",
                sources=[],
                next_action=None,
                session_id=request.session_id,
            ), []

        # Step 2: Knowledge Retrieval from RAG Vector DB
        rag_chunks: list[RetrievedChunk] = []
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

        # Step 3: Check if Live Web Search is justified (Current/Time-Sensitive or Complex Query)
        web_results: List[Dict[str, Any]] = []
        trigger_web_search = intent in TIME_SENSITIVE_INTENTS or not rag_chunks

        if trigger_web_search:
            try:
                web_results = search_web_knowledge(message, max_results=3)
            except Exception as exc:
                logger.warning(f"Web search execution exception: {exc}")
                web_results = []

        # Step 4: Extract and combine sources
        sources_list: list[dict[str, Any]] = []
        seen_urls = set()

        for chunk in rag_chunks:
            title = chunk.get("title") or "Official Knowledge Base"
            url = chunk.get("source_url") or ""
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
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources_list.append({
                    "title": web_item.get("title") or "Live Government Notice",
                    "source_name": web_item.get("source_name") or "Government Web Portal",
                    "source_url": url,
                    "document_id": None,
                })

        primary_source = sources_list[0]["title"] if sources_list else "SahkaarSetu Cooperative Knowledge"

        # Step 5: Format context chunks for Groq prompt
        combined_context_text = ""
        if rag_chunks:
            combined_context_text += "--- STABLE OFFICIAL RAG KNOWLEDGE CONTEXT ---\n"
            for idx, chunk in enumerate(rag_chunks, 1):
                combined_context_text += f"[{idx}] {chunk.get('title')}: {chunk.get('content')}\n"

        if web_results:
            combined_context_text += "\n--- CURRENT LIVE WEB RESEARCH CONTEXT ---\n"
            for idx, item in enumerate(web_results, 1):
                combined_context_text += f"[Web-{idx}] {item.get('title')} ({item.get('source_name')}): {item.get('snippet')}\n"

        if not combined_context_text.strip():
            combined_context_text = "NO SPECIFIC CONTEXT FOUND IN DATABASE. USE GENERAL COOPERATIVE GOVERNANCE KNOWLEDGE GROUNDED IN INDIAN LAWS AND PACS RULES."

        # Step 6: Construct Deep Structured Prompt for Groq
        prompt = build_grounded_prompt(
            message=message,
            language=language,
            intent=intent,
            context_chunks=rag_chunks,
            response_mode=resp_mode,
        )

        if web_results:
            prompt += f"\n\nLIVE WEB RESEARCH CONTEXT:\n{combined_context_text}"

        # Deep structured answer guidance for agricultural & credit queries
        if any(w in message.lower() for w in ["acre", "land", "loan", "कर्ज", "पिक कर्ज", "जमीन", "एकड"]):
            prompt += (
                "\n\nSPECIAL GUIDANCE FOR LAND / FARMING LOAN QUERY:\n"
                "Explain comprehensively and helpfully:\n"
                "1. Relevant credit options (PACS Short-term Crop Loan / Kisan Credit Card / KCC)\n"
                "2. Factors determining eligibility (Land ownership 7/12 extract, active PACS membership share)\n"
                "3. Documents needed (7/12 & 8A extracts, Aadhaar, PAN, Bank Passbook, Society Membership)\n"
                "4. Step-by-step application process\n"
                "5. Important questions to ask at the PACS or bank branch\n"
                "6. Relevant government support schemes (Interest Subvention Scheme / Subsidies)\n"
                "7. Important conditions or what to verify next\n"
                "Format using clear headings and bullet points."
            )

        # Step 7: Invoke Groq LLM API Engine
        max_tokens = 300 if resp_mode == "voice" else 1000
        answer_text, used_model = query_groq_llm(
            system_instruction=RAG_SYSTEM_INSTRUCTION,
            user_prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.2,
        )

        if not answer_text:
            logger.warning("[AI PROVIDER] GROQ returned empty response. Falling back to default error text.")
            answer_text = NO_KNOWLEDGE_FALLBACK.get(language, NO_KNOWLEDGE_FALLBACK["en"])

        if resp_mode == "voice" and answer_text:
            answer_text = clean_speech_text(answer_text)

        # Structured Development Audit Logging
        logger.info(
            "\n========================================================\n"
            f"[AI PROVIDER] GROQ\n"
            f"[MODEL] {used_model}\n"
            f"[STT PROVIDER] WEB_SPEECH_API\n"
            f"[TTS PROVIDER] BROWSER_SPEECH_SYNTHESIS\n"
            f"[QUERY] '{message}'\n"
            f"[LANGUAGE] {language}\n"
            f"[INTENT] {intent}\n"
            f"[RAG TRIGGERED] {bool(rag_chunks)} ({len(rag_chunks)} chunks)\n"
            f"[WEB SEARCH TRIGGERED] {bool(web_results)} ({len(web_results)} results)\n"
            f"[RESPONSE MODE] {resp_mode}\n"
            "========================================================"
        )

        response_obj = QueryResponse(
            answer=answer_text,
            language=language,
            intent=intent,
            source=primary_source,
            next_action=None,
            session_id=request.session_id,
        )

        return response_obj, sources_list
