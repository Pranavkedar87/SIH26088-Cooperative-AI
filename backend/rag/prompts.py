"""
Grounded system instructions and prompt formatting for RAG.
"""
from __future__ import annotations

from typing import Any

_LANG_NAME: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "gu": "Gujarati",
    "bn": "Bengali",
    "pa": "Punjabi",
    "ml": "Malayalam",
}

DIRECT_RESPONSES: dict[str, dict[str, str]] = {
    "CASUAL_GREETING": {
        "mr": "नमस्कार! मी SahkaarSetu आहे. तुम्ही मला कोणताही प्रश्न विचारू शकता — सरकारी योजना, शेती, विज्ञान, इतिहास, तंत्रज्ञान किंवा कोणताही विषय.",
        "hi": "नमस्ते! मैं SahkaarSetu हूँ। आप मुझसे कोई भी सवाल पूछ सकते हैं — सरकारी योजनाएं, कृषि, विज्ञान, इतिहास, तकनीक या कोई भी विषय।",
        "en": "Hello! I'm SahkaarSetu AI. You can ask me anything — government schemes, agriculture, science, history, technology, or any general topic. How can I help you?",
    },
    "CASUAL_THANKS": {
        "mr": "आपले स्वागत आहे! तुम्हाला आणखी काही मदत हवी असल्यास नक्की विचारू शकता.",
        "hi": "आपका स्वागत है! यदि आपको किसी अन्य सहायता की आवश्यकता हो, तो अवश्य पूछें।",
        "en": "You are most welcome! Feel free to ask if you need any more assistance.",
    },
    "CASUAL_IDENTITY": {
        "mr": "मी SahkaarSetu AI आहे — एक बहुभाषिक AI असिस्टंट जो कोणत्याही विषयावर उत्तर देऊ शकतो: सरकारी योजना, शेती, PACS, विज्ञान, इतिहास आणि बरेच काही.",
        "hi": "मैं SahkaarSetu AI हूँ — एक बहुभाषी AI सहायक जो किसी भी विषय पर जवाब दे सकता है: सरकारी योजनाएं, कृषि, PACS, विज्ञान, इतिहास और बहुत कुछ।",
        "en": "I am SahkaarSetu AI — a multilingual AI assistant that can answer any question: government schemes, agriculture, PACS, science, history, technology, and much more.",
    },
    "UNCLEAR": {
        "mr": "नक्की. तुम्हाला कशाबद्दल मदत हवी आहे? कोणताही विषय विचारा.",
        "hi": "जी, आपको किस विषय में सहायता चाहिए? कोई भी सवाल पूछें।",
        "en": "Sure! What would you like to know? Feel free to ask about anything.",
    },
}

RAG_SYSTEM_INSTRUCTION = (
    "You are SahkaarSetu AI, an expert, friendly, conversational assistant for government schemes, cooperative laws, PACS, and agriculture.\n"
    "\n"
    "🌐 LANGUAGE RULE (HIGHEST PRIORITY):\n"
    "- You MUST detect the language the user is typing in and reply in THAT EXACT SAME LANGUAGE.\n"
    "- If the user writes in Marathi → reply 100% in Marathi.\n"
    "- If the user writes in Hindi → reply 100% in Hindi.\n"
    "- If the user writes in English → reply 100% in English.\n"
    "- NEVER mix languages in your response. NEVER default to English when the question is in Marathi or Hindi.\n"
    "- The MANDATORY LANGUAGE RULE in the user message overrides everything else.\n"
    "\n"
    "CONVERSATIONAL PRINCIPLE:\n"
    "- Make your direct answer conversational and helpful (like ChatGPT). Explain the core answer directly.\n"
    "- If the user asks a broad or introductory question, give a clear overview and naturally mention helpful details you can explain.\n"
    "- Do NOT output artificial canned greetings like 'Welcome to SahkaarSetu' or robotic prefixes like 'Direct Answer:'.\n"
    "\n"
    "CONDITIONAL SECTIONS:\n"
    "- Include sections ONLY when they provide distinct value (e.g. key facts, numbered procedure steps, or required documents). If a simple direct answer suffices, keep 'sections' minimal (0 to 1 section).\n"
    "\n"
    "SAFETY & FACTUAL GROUNDING:\n"
    "- Base scheme benefits, eligibility, deadlines, and documents strictly on the retrieved context.\n"
    "- NEVER invent schemes, numbers, fees, or documents. If information is not in context, state that clearly.\n"
    "- For general knowledge questions, answer accurately and directly.\n"
    "- Do NOT output internal thoughts or <think> tags. Immediately output valid JSON.\n"
    "\n"
    "MULTILINGUAL & VOICE:\n"
    "- All content values (direct_answer, section titles, item text, spoken_answer, followups) MUST be in the user's requested language.\n"
    "- JSON keys must remain in English.\n"
    "- 'spoken_answer' must be 1 natural conversational sentence suitable for TTS voice playback.\n"
    "\n"
    "JSON OUTPUT FORMAT:\n"
    "Return ONLY valid JSON matching this schema:\n"
    "{\n"
    '  "direct_answer": "<Conversational direct answer in target language>",\n'
    '  "answer_focus": "<overview|procedure|documents|contact|eligibility|deadline|next_step|complaint|general>",\n'
    '  "sections": [\n'
    '    {\n'
    '      "type": "<key_facts|steps|documents|where_to_go|details|next_action>",\n'
    '      "title": "<Short section title in target language>",\n'
    '      "items": [\n'
    '        {"label": "<short key/badge>", "value": "<concise fact under 12 words>"} OR\n'
    '        {"name": "<item/doc/office name>", "description": "<brief description>"}\n'
    '      ]\n'
    '    }\n'
    '  ],\n'
    '  "spoken_answer": "<1 natural sentence for TTS audio in target language>",\n'
    '  "suggested_followups": [\n'
    '    {"label": "<2-5 words chip in target language>", "query": "<full contextual question in target language>"}\n'
    '  ]\n'
    "}\n"
    "RULES: Keep JSON compact (1-2 sections max). Suggested follow-ups must be relevant and contextual."
)


def build_grounded_prompt(
    message: str,
    language: str,
    intent: str,
    context_chunks: list[dict[str, Any]],
    response_mode: str = "text",
) -> str:
    """Format prompt with retrieved context chunks."""
    lang_name = _LANG_NAME.get(language, "English")

    if context_chunks:
        formatted_context = ""
        for idx, chunk in enumerate(context_chunks, 1):
            title = chunk.get("title", "Official Document")
            source = chunk.get("source_name", "Official Source")
            content = chunk.get("content", "")
            formatted_context += f"--- SOURCE [{idx}]: {title} ({source}) ---\n{content}\n\n"
    else:
        formatted_context = "NO SPECIFIC KNOWLEDGE RETRIEVED. Answer from your general knowledge."

    base_prompt = (
        f"Target language: {lang_name}\n"
        f"Detected intent: {intent}\n\n"
        f"RETRIEVED KNOWLEDGE CONTEXT:\n"
        f"{formatted_context}\n"
        f"USER QUESTION:\n{message}\n\n"
        f"Instruction: Answer in {lang_name} following the JSON schema. Be concise and factual."
    )

    if response_mode == "voice":
        base_prompt += (
            f"\nVOICE MODE: Keep 'spoken_answer' strictly 1 natural sentence in {lang_name}."
        )

    return base_prompt


# Neutral Technical Failure Fallback Messages (No Manual Factual Claims)
TECHNICAL_ERROR_FALLBACK: dict[str, str] = {
    "en": "I am unable to process your request right now. Please try again in a moment.",
    "hi": "मैं अभी आपके अनुरोध को संसाधित करने में असमर्थ हूँ। कृपया कुछ देर बाद पुनः प्रयास करें।",
    "mr": "मी आत्ता तुमची विनंती प्रक्रिया करू शकत नाही. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.",
}

NO_KNOWLEDGE_FALLBACK = TECHNICAL_ERROR_FALLBACK
NO_KNOWLEDGE_FALLBACK_WITH_STATE = TECHNICAL_ERROR_FALLBACK

def get_intent_fallback(intent: str, language: str = "mr", focus: str = "OVERVIEW") -> str:
    """Returns neutral technical error message when LLM generation fails."""
    lang_code = language.lower() if language in ["en", "hi", "mr"] else "mr"
    return TECHNICAL_ERROR_FALLBACK.get(lang_code, TECHNICAL_ERROR_FALLBACK["en"])
