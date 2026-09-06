"""
RAG Pipeline orchestrator.

Coordinates Intent Detection -> Retrieval -> Grounded Generation -> Source Extraction.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Optional


from google import genai
from google.genai import types as genai_types

from app.config import get_settings
from app.providers.gemini_provider import _classify_intent, _ERROR_ANSWER
from app.schemas.query import IntentCode, QueryRequest, QueryResponse
from rag.prompts import RAG_SYSTEM_INSTRUCTION, build_grounded_prompt, NO_KNOWLEDGE_FALLBACK
from rag.retriever import retrieve_relevant_knowledge, RetrievedChunk

logger = logging.getLogger(__name__)

# Intents that require strict knowledge retrieval
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
    # Strip URLs
    cleaned = re.sub(r'https?://\S+', '', text)
    # Strip markdown headings, bold, italics, code
    cleaned = re.sub(r'#+\s*', '', cleaned)
    cleaned = re.sub(r'\*+', '', cleaned)
    cleaned = re.sub(r'_+', '', cleaned)
    cleaned = re.sub(r'`+', '', cleaned)
    cleaned = re.sub(r'^\s*[-*+]\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*\d+\.\s+', '', cleaned, flags=re.MULTILINE)
    # Strip markdown link syntax [label](url)
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


class RAGPipeline:
    """Orchestrates end-to-end grounded query answering."""

    _client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if RAGPipeline._client is None:
            settings = get_settings()
            api_key = settings.gemini_api_key.strip()
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY is not configured in backend/.env")
            RAGPipeline._client = genai.Client(api_key=api_key)
        return RAGPipeline._client

    async def process_query(self, request: QueryRequest) -> tuple[QueryResponse, list[dict[str, Any]]]:
        """
        Process user query through RAG pipeline.

        Returns:
            (QueryResponse, sources_list)
        """
        message = request.message.strip()
        language = request.language
        resp_mode = getattr(request, "response_mode", "text") or "text"

        # 1. Intent classification
        intent = _classify_intent(message)

        # FAST PATH FOR CASUAL GREETINGS, THANKS, IDENTITY & UNCLEAR:
        # MUST NOT TRIGGER VECTOR SEARCH OR RAG RETRIEVAL
        CASUAL_INTENTS = {"CASUAL_GREETING", "CASUAL_THANKS", "CASUAL_IDENTITY", "UNCLEAR", "GREETING"}
        if intent in CASUAL_INTENTS:
            from rag.prompts import DIRECT_RESPONSES
            mapped_intent = "CASUAL_GREETING" if intent == "GREETING" else intent
            lang_dict = DIRECT_RESPONSES.get(mapped_intent, DIRECT_RESPONSES["CASUAL_GREETING"])
            ans_text = lang_dict.get(language) or lang_dict.get("mr") or lang_dict["en"]

            logger.info(
                "[VOICE]\nTranscript: %s\nDetected language: %s\nQuery type: %s\nIntent: %s\nRAG triggered: false\nLLM: Direct Fast-Path\nResponse language: %s\nResponse mode: %s\nTTS language: %s",
                message, language, intent, intent, language, resp_mode, language
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

        # 2. Knowledge Retrieval (Domain Queries Only)
        try:
            chunks: list[RetrievedChunk] = retrieve_relevant_knowledge(
                query=message,
                language=language,
                intent=intent,
                top_k=4,
                match_threshold=0.45,
            )
        except Exception as exc:
            logger.error("Knowledge retrieval failed (falling back to controlled refusal): %s", exc)
            chunks = []

        logger.info("RAG Pipeline | retrieved %d chunks for intent %s", len(chunks), intent)

        # 3. Handle No-Context for specific domain intents
        if not chunks and intent in STRICT_KNOWLEDGE_INTENTS:
            logger.info("No matching knowledge found for strict intent %s. Returning controlled fallback.", intent)
            fallback_text = NO_KNOWLEDGE_FALLBACK.get(language, NO_KNOWLEDGE_FALLBACK["en"])

            return QueryResponse(
                answer=fallback_text,
                language=language,
                intent=intent,
                source=None,
                next_action="VERIFY_WITH_OFFICIAL",
                session_id=request.session_id,
            ), []

        # 4. Extract unique sources from chunks
        sources_list: list[dict[str, Any]] = []
        seen_titles = set()

        for chunk in chunks:
            title = chunk.get("title") or "Official Source"
            if title not in seen_titles:
                seen_titles.add(title)
                sources_list.append({
                    "title": title,
                    "source_name": chunk.get("source_name"),
                    "source_url": chunk.get("source_url"),
                    "document_id": chunk.get("document_id"),
                })

        primary_source = sources_list[0]["title"] if sources_list else None

        # 5. Build grounded prompt & call Gemini using fast candidate fallback
        answer = None
        used_model = "fallback"
        client = self._get_client()
        prompt = build_grounded_prompt(message, language, intent, chunks, response_mode=resp_mode)

        model_candidates = [
            "gemini-3.5-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.6-flash",
            "gemini-2.5-flash",
        ]

        max_tokens = 250 if resp_mode == "voice" else 1024

        for model_name in model_candidates:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=RAG_SYSTEM_INSTRUCTION,
                        temperature=0.2,  # Low temperature for strict factual grounding
                        max_output_tokens=max_tokens,
                    ),
                )
                if response and response.text:
                    answer = response.text.strip()
                    if answer:
                        used_model = model_name
                        logger.info("RAG generation succeeded using model '%s'", model_name)
                        break
            except Exception as exc:
                logger.warning("Model '%s' generation failed/quota hit (%s). Trying next candidate...", model_name, exc)
                continue

        if not answer:
            logger.warning("Gemini returned empty response text or failed generation.")
            answer = _ERROR_ANSWER.get(language, _ERROR_ANSWER["en"])
            sources_list = []
            primary_source = None

        if resp_mode == "voice" and answer:
            answer = clean_speech_text(answer)

        logger.info(
            "[VOICE]\nTranscript: %s\nDetected language: %s\nQuery type: DOMAIN\nIntent: %s\nRAG triggered: true\nRAG collection: %s\nRetrieved chunks: %d\nLLM model: %s\nResponse language: %s\nResponse mode: %s\nTTS language: %s",
            message, language, intent, intent, len(chunks), used_model, language, resp_mode, language
        )

        response_obj = QueryResponse(
            answer=answer,
            language=language,
            intent=intent,
            source=primary_source,
            next_action=None,
            session_id=request.session_id,
        )

        return response_obj, sources_list



