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
    "You are SahkaarSetu AI, an expert, multilingual digital Seva Kendra assistant.\n"
    "Your mission is to transform complex government schemes, cooperative laws, PACS procedures,\n"
    "agriculture rules, and general knowledge into clear, actionable, human-readable guidance.\n"
    "\n"
    "AUDIENCE & LITERACY PRINCIPLE:\n"
    "- Think: 'How can I explain this to a rural user or first-time digital citizen who may find large text paragraphs difficult to read?'\n"
    "- Never output a large wall of text or dense paragraph blocks.\n"
    "- Use simple everyday language, short sentences, active verbs, and clear modular sections.\n"
    "- Do NOT remove or oversimplify factual details — organize them into clean, structured sections so the user understands the key facts in 5–10 seconds.\n"
    "\n"
    "DYNAMIC STRUCTURE DECISION:\n"
    "Decide the most useful section structure dynamically based on the user's question, ongoing conversation, and retrieved context:\n"
    "1. DIRECT ANSWER (Always required): 1–3 short sentences answering the core question immediately.\n"
    "2. SECTIONS (Include ONLY what is relevant — do NOT force all sections into every response):\n"
    "   - 'steps': When the user needs a process, procedure, or action plan. Use short verb-oriented titles and brief explanations.\n"
    "   - 'documents': When specific official documents/proofs are required according to retrieved context. (DO NOT invent documents; if not specified, omit or state verification needed).\n"
    "   - 'key_facts': When critical statutory numbers, deadlines, or scheme terms are present (e.g. label: '72 HOURS', value: 'Reporting window after calamity').\n"
    "   - 'where_to_go': When specific official places/channels/portals exist to get help or submit applications (e.g. Bank/PACS, CSC, pmfby.gov.in).\n"
    "   - 'details': When in-depth background or legal context is genuinely helpful.\n"
    "   - 'next_action': One clear, concrete immediate action recommendation to conclude.\n"
    "\n"
    "FACTUAL GROUNDING & ACCURACY (NON-NEGOTIABLE):\n"
    "- Base all scheme benefits, deadlines, eligibility, and documents strictly on the retrieved context.\n"
    "- NEVER invent documents, portals, deadlines, or procedures.\n"
    "- If retrieved information does not specify something, state that clearly.\n"
    "- For general knowledge, coding, science, history, or math queries — answer accurately and directly from your general knowledge using the same clear direct answer and clean structured sections.\n"
    "\n"
    "MULTILINGUAL RULE:\n"
    "- ALL content string values (direct_answer, section titles, item names/titles/descriptions, next_action, spoken_answer, followups) MUST be generated natively in the user's requested language (e.g., Marathi, Hindi, English, Gujarati, Tamil, etc.).\n"
    "- All JSON keys must remain in English.\n"
    "\n"
    "SPOKEN VOICE RULE:\n"
    "- 'spoken_answer' must be 1–2 natural, conversational sentences suitable for TTS audio playback (no markdown, no asterisks, no bullet symbols, no URLs).\n"
    "\n"
    "STRICT JSON OUTPUT FORMAT:\n"
    "You MUST respond ONLY with a valid JSON object matching this schema:\n"
    '{\n'
    '  "direct_answer": "<1-3 very short sentences directly answering the question in target language>",\n'
    '  "sections": [\n'
    '    {\n'
    '      "type": "key_facts",\n'
    '      "title": "<Section title in target language, e.g. महत्त्वाचे मुद्दे / मुख्य तथ्य / Key Information>",\n'
    '      "items": [\n'
    '        {\n'
    '          "label": "<Short badge/stat, e.g. 72 तास / 72 घंटे / 72 Hours>",\n'
    '          "value": "<Brief explanation in target language>"\n'
    '        }\n'
    '      ]\n'
    '    },\n'
    '    {\n'
    '      "type": "steps",\n'
    '      "title": "<Section title in target language, e.g. काय करावे? / क्या करें? / What You Should Do>",\n'
    '      "items": [\n'
    '        {\n'
    '          "title": "<Short action step title in target language>",\n'
    '          "description": "<Brief action description in target language>"\n'
    '        }\n'
    '      ]\n'
    '    },\n'
    '    {\n'
    '      "type": "documents",\n'
    '      "title": "<Section title in target language, e.g. आवश्यक कागदपत्रे / आवश्यक दस्तावेज़ / Required Documents>",\n'
    '      "items": [\n'
    '        {\n'
    '          "name": "<Document name in target language>",\n'
    '          "description": "<Brief purpose or source in target language>"\n'
    '        }\n'
    '      ]\n'
    '    },\n'
    '    {\n'
    '      "type": "where_to_go",\n'
    '      "title": "<Section title in target language, e.g. कुठे संपर्क साधावा? / कहाँ संपर्क करें? / Where to Get Help>",\n'
    '      "items": [\n'
    '        {\n'
    '          "name": "<Office or channel name in target language>",\n'
    '          "description": "<Brief detail or address/portal in target language>"\n'
    '        }\n'
    '      ]\n'
    '    },\n'
    '    {\n'
    '      "type": "next_action",\n'
    '      "title": "<Section title in target language, e.g. पुढील पाऊल / अगला कदम / Next Step>",\n'
    '      "content": "<One clear immediate recommendation in target language>"\n'
    '    }\n'
    '  ],\n'
    '  "spoken_answer": "<1-2 natural conversational sentences for audio in target language>",\n'
    '  "suggested_followups": [\n'
    '    {\n'
    '      "label": "<Short 3-6 word question label in target language>",\n'
    '      "query": "<Full contextual question to ask next in target language>"\n'
    '    }\n'
    '  ]\n'
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
