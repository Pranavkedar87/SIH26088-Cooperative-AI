"""
RAG Pipeline orchestrator.

Coordinates Intent Detection -> Retrieval -> Grounded Generation -> Source Extraction.
"""
from __future__ import annotations

import asyncio
import logging
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

        # 1. Intent classification
        intent = _classify_intent(message)
        logger.info("RAG Pipeline | intent=%s | lang=%s | msg=%.60s", intent, language, message)

        # 2. Knowledge Retrieval
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
            # Check if general query vs specific factual query
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

        # 5. Build grounded prompt & call Gemini
        answer = None
        client = self._get_client()
        prompt = build_grounded_prompt(message, language, intent, chunks)

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=RAG_SYSTEM_INSTRUCTION,
                        temperature=0.2,  # Low temperature for strict factual grounding
                        max_output_tokens=1024,
                    ),
                )
                if response and response.text:
                    answer = response.text.strip()
                    if answer:
                        break
            except Exception as exc:
                is_rate_limit = "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc) or "quota" in str(exc).lower()
                if is_rate_limit and attempt < 2:
                    logger.warning("Gemini rate limit hit (429). Retrying in 15s (attempt %d/3)...", attempt + 1)
                    await asyncio.sleep(15.0)
                    continue
                logger.exception("Gemini API or generation error during RAG generation: %s", exc)
                break

        if not answer:
            logger.warning("Gemini returned empty response text or failed generation.")
            answer = _ERROR_ANSWER.get(language, _ERROR_ANSWER["en"])
            sources_list = []
            primary_source = None

        response_obj = QueryResponse(
            answer=answer,
            language=language,
            intent=intent,
            source=primary_source,
            next_action=None,
            session_id=request.session_id,
        )

        return response_obj, sources_list



