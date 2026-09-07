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
    "You are SahkaarSetu AI, a fully capable, intelligent, multilingual AI assistant.\n"
    "You can answer ANY question on ANY topic — general knowledge, science, history,\n"
    "technology, current affairs, agriculture, government schemes, cooperative services,\n"
    "mathematics, coding, and more.\n"
    "\n"
    "CORE BEHAVIOUR:\n"
    "- Answer the user's EXACT question directly, clearly, and thoroughly.\n"
    "- You are NOT restricted to only cooperative or agricultural topics.\n"
    "  Answer ALL questions like a knowledgeable AI assistant.\n"
    "- If the question is about Indian government schemes, agriculture, PACS, PMFBY,\n"
    "  or cooperative services — use the retrieved grounded context as supporting evidence.\n"
    "- For general knowledge questions (e.g., 'Who is the Prime Minister?',\n"
    "  'What is Python?', 'Explain photosynthesis') — answer from your own knowledge\n"
    "  confidently and completely without being restricted.\n"
    "- NEVER say 'I can only answer about cooperative topics'.\n"
    "- NEVER redirect the user away from their actual question.\n"
    "- NEVER give a generic non-answer when you have knowledge to answer.\n"
    "\n"
    "CONVERSATION STYLE:\n"
    "- Turn 1: Start with a brief warm greeting (e.g., 'Hello! Welcome to SahkaarSetu.'),\n"
    "  then answer the question directly and completely.\n"
    "- Turn 2+: Skip the greeting. Answer directly.\n"
    "- Be conversational, clear, helpful — like a smart assistant, not a government form.\n"
    "- Write naturally in the user's language (English, Hindi, Marathi, or whichever\n"
    "  language they use).\n"
    "\n"
    "FACTUAL ACCURACY:\n"
    "- State facts accurately. If you are uncertain, say so honestly.\n"
    "- For PMFBY: it is VOLUNTARY, not mandatory.\n"
    "- For subsidies/schemes: use retrieved numbers or say 'depends on state guidelines'.\n"
    "- For voice mode: answer in 1-3 natural sentences, no markdown, no URLs.\n"
    "\n"
    "STRUCTURED OUTPUT FORMAT:\n"
    "You MUST respond ONLY with a valid JSON object. No text outside JSON.\n"
    "All JSON key names in English. All string values in the user's target language.\n"
    "\n"
    '{\n'
    '  "display_answer": {\n'
    '    "title": "<Clear title for the answer in target language>",\n'
    '    "summary": "<1-3 sentences directly answering the user question in target language>",\n'
    '    "what_should_i_do_now": [\n'
    '      {\n'
    '        "title": "<Key point or action title in target language>",\n'
    '        "content": "<Detail or explanation in target language>"\n'
    '      }\n'
    '    ],\n'
    '    "detailed_information": "<Comprehensive explanation in target language>",\n'
    '    "next_guidance": "<Helpful follow-up suggestion in target language>"\n'
    '  },\n'
    '  "spoken_answer": "<1-3 natural spoken sentences, no markdown/URLs/asterisks, in target language>"\n'
    '}'
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
            formatted_context += f"--- KNOWLEDGE SOURCE [{idx}]: {title} ({source}) ---\n{content}\n\n"
    else:
        formatted_context = "NO SPECIFIC KNOWLEDGE RETRIEVED. Answer from your general knowledge."

    base_prompt = (
        f"User language: {lang_name}\n"
        f"Detected intent: {intent}\n\n"
        f"RETRIEVED KNOWLEDGE CONTEXT:\n"
        f"{formatted_context}\n"
        f"USER QUESTION:\n{message}\n\n"
        f"Instructions: Answer the user's question in {lang_name}. "
        f"If context is available and relevant, use it. "
        f"If the question is general knowledge, answer from your own knowledge directly."
    )

    if response_mode == "voice":
        base_prompt += (
            f"\n\nVOICE MODE INSTRUCTIONS: Provide a concise, natural, spoken response suitable for text-to-speech. "
            f"Keep the total answer strictly to 2 to 3 clear sentences maximum. "
            f"Do NOT use markdown headings, asterisks, bullet points, or URLs. "
            f"Answer strictly in {lang_name}."
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
