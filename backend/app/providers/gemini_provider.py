"""
Gemini AI provider — stub implementation for Milestone 1.

In Milestone 2 this will:
  - Load the Gemini API key from settings.
  - Call the Gemini Flash / Pro model.
  - Perform intent classification.
  - Inject RAG context from the knowledge base.
"""
from __future__ import annotations
import logging
from app.providers.ai_provider import AIProvider
from app.schemas.query import IntentCode, QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

# Placeholder responses per language — replaced by real Gemini calls in M2.
_PLACEHOLDER: dict[str, str] = {
    "en": (
        "Hello! I am the Cooperative AI Assistant. "
        "I will help you with cooperative laws, schemes, and grievances. "
        "(Gemini integration coming in Milestone 2.)"
    ),
    "hi": (
        "नमस्ते! मैं सहकारी AI सहायक हूँ। "
        "मैं सहकारी कानूनों, योजनाओं और शिकायतों में आपकी मदद करूँगा। "
        "(Gemini एकीकरण Milestone 2 में आएगा।)"
    ),
    "mr": (
        "नमस्कार! मी सहकारी AI सहाय्यक आहे। "
        "मी सहकारी कायदे, योजना आणि तक्रारींमध्ये तुमची मदत करेन। "
        "(Gemini एकत्रीकरण Milestone 2 मध्ये येईल.)"
    ),
}


class GeminiProvider(AIProvider):
    """
    Concrete Gemini implementation of AIProvider.

    Milestone 1: Returns a placeholder response.
    Milestone 2: Will call google-generativeai SDK with RAG context.
    """

    async def answer_query(self, request: QueryRequest) -> QueryResponse:
        logger.info(
            "GeminiProvider.answer_query | lang=%s | msg=%.80s",
            request.language,
            request.message,
        )

        answer = _PLACEHOLDER.get(request.language, _PLACEHOLDER["en"])

        return QueryResponse(
            answer=answer,
            language=request.language,
            intent="GENERAL_COOPERATIVE",
            source=None,
            next_action=None,
        )
