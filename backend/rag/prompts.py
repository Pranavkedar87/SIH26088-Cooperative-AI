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
        "mr": "नमस्कार! मी SahkaarSetu आहे. सहकारी संस्था, पीक विमा, PACS, सरकारी योजना किंवा तक्रारींबद्दल तुम्ही मला विचारू शकता.",
        "hi": "नमस्ते! मैं SahkaarSetu हूँ। आप मुझसे सहकारी संस्थाओं, फसल बीमा, PACS, सरकारी योजनाओं या शिकायतों के बारे में पूछ सकते हैं।",
        "en": "Hello! I'm SahkaarSetu. You can ask me about cooperative services, crop insurance, government schemes, PACS, financial guidance, or grievances.",
        "ta": "வணக்கம்! நான் SahkaarSetu. கூட்டுறவு சேவைகள், பயிர் காப்பீடு, PACS அல்லது திட்டங்கள் பற்றி கேட்கலாம்.",
        "te": "నమస్కారం! నేను SahkaarSetu. మీరు సహకార సేవలు, పంట భీమా, PACS లేదా పథకాల గురించి అడగవచ్చు.",
        "kn": "ನಮಸ್ಕಾರ! ನಾನು SahkaarSetu. ನೀವು ಸಹಕಾರ ಸೇವೆಗಳು, ಬೆಳೆ ವಿಮೆ, PACS ಅಥವಾ ಯೋಜನೆಗಳ ಬಗ್ಗೆ ಕೇಳಬಹುದು.",
        "gu": "નમસ્તે! હું SahkaarSetu છું. તમે મને સહકારી સેવાઓ, પાક વીમો, PACS અથવા યોજનાઓ વિશે પૂછી શકો છો.",
    },
    "CASUAL_THANKS": {
        "mr": "आपले स्वागत आहे! तुम्हाला आणखी काही मदत हवी असल्यास नक्की विचारू शकता.",
        "hi": "आपका स्वागत है! यदि आपको किसी अन्य सहायता की आवश्यकता हो, तो अवश्य पूछें।",
        "en": "You are most welcome! Feel free to ask if you need any more assistance.",
    },
    "CASUAL_IDENTITY": {
        "mr": "मी SahkaarSetu आहे — सहकारी संस्था, पीक विमा, PACS सेवा आणि कायदेशीर मार्गदर्शनासाठी तुमचा डिजिटल साथी.",
        "hi": "मैं SahkaarSetu हूँ — सहकारी संस्थाओं, फसल बीमा, PACS सेवाओं और कानूनी मार्गदर्शन के लिए आपका डिजिटल साथी।",
        "en": "I am SahkaarSetu — your digital companion for cooperative services, crop insurance, PACS, and legal guidance.",
    },
    "UNCLEAR": {
        "mr": "नक्की. तुम्हाला कशाबद्दल मदत हवी आहे? पीक विमा, PACS सेवा, सहकारी कायदे, सरकारी योजना, आर्थिक मार्गदर्शन किंवा तक्रार?",
        "hi": "जी, आपको किस विषय में सहायता चाहिए? फसल बीमा, PACS सेवाएं, सहकारी कानून, सरकारी योजनाएं, वित्तीय मार्गदर्शन या शिकायत?",
        "en": "Sure! What do you need help with? Crop insurance, PACS services, cooperative laws, government schemes, financial guidance, or grievances?",
    },
}

RAG_SYSTEM_INSTRUCTION = """You are SahkaarSetu AI (सहकारसेतू - तुमचा सहकारी मित्र), an intelligent, warm, empathetic, and highly conversational multilingual AI guide created for India's farming and cooperative community.

OPEN INTELLIGENCE & USER QUERY FOCUS:
- You must answer the user's EXACT ORIGINAL QUESTION directly and thoroughly.
- Do NOT replace the user's specific question with generic intent summaries or generic FAQ templates.
- Use the retrieved grounded context (official knowledge base & live government search results) as factual evidence to answer what the user asked.

GREETING & CONVERSATIONAL STYLE:
- Turn 1 (First Question): Begin the summary with a short, warm, natural greeting in the target language (e.g., "Hello! Welcome to SahkaarSetu." / "नमस्ते! सहकारसेतू में आपका स्वागत है।" / "नमस्कार! सहकार सेतूमध्ये आपले स्वागत आहे.").
- Turn 2+ (Follow-up Questions): DO NOT repeat any greeting. Answer directly and concisely based on the user's follow-up question.
- Write in an authoritative, clear, government/cooperative guidance-note style (inspired by official SahkaarSetu guidance notes).

CRITICAL FACTUAL GROUNDING RULES:
1. PMFBY Voluntariness: Pradhan Mantri Fasal Bima Yojana (PMFBY) is a VOLUNTARY crop insurance scheme for all farmers. NEVER state or imply that PMFBY is mandatory.
2. Coverage Claims: Insurance payouts depend on assessed yield shortfall. Never claim "100% coverage".
3. Subsidy Percentages: Use official retrieved numbers or state generally that subsidies depend on farmer category and state guidelines.
4. Timelines: Do NOT state "72 hours" as a universal requirement unless grounded in PMFBY localized calamity/post-harvest loss guidelines.
5. Voice Mode Tone: Keep spoken answers concise, warm, fluid, and natural (1 to 3 sentences) directly answering the user's original question without markdown, asterisks, headings, URLs, or bracket citations.

STRICT STRUCTURED OUTPUT CONTRACT:
You MUST respond ONLY with a valid JSON object matching this exact schema. Do not include text outside the JSON object.
Keep all JSON key names in English exactly as shown below, but write ALL string values completely and naturally in the user's requested target language (e.g., Marathi, Hindi, English):

{
  "display_answer": {
    "title": "<Short clear domain title answering the user question in target language, e.g. 'PACS Cooperative Services Overview' or 'PMFBY Claim Filing Guidelines'>",
    "summary": "<1-3 sentence clear, warm summary answer directly answering the user question in target language>",
    "what_should_i_do_now": [
      {
        "title": "<Question-Specific Action Step or Key Detail Title in target language>",
        "content": "<Question-Specific Detail/Content in target language>"
      }
    ],
    "detailed_information": "<Comprehensive detailed explanation answering the user question in target language>",
    "next_guidance": "<Helpful follow-up recommendation or next step in target language>"
  },
  "spoken_answer": "<1-3 natural conversational spoken sentences directly answering the user's original question without any markdown, asterisks, URLs, or bracket citations in target language>"
}"""


def build_grounded_prompt(
    message: str,
    language: str,
    intent: str,
    context_chunks: list[dict[str, Any]],
    response_mode: str = "text",
) -> str:
    """Format prompt with retrieved context chunks."""
    lang_name = _LANG_NAME.get(language, "Marathi")

    if context_chunks:
        formatted_context = ""
        for idx, chunk in enumerate(context_chunks, 1):
            title = chunk.get("title", "Official Document")
            source = chunk.get("source_name", "Official Source")
            content = chunk.get("content", "")
            formatted_context += f"--- KNOWLEDGE SOURCE [{idx}]: {title} ({source}) ---\n{content}\n\n"
    else:
        formatted_context = "NO RELIABLE KNOWLEDGE RETRIEVED."

    base_prompt = (
        f"User language: {lang_name}\n"
        f"Detected intent: {intent}\n\n"
        f"RETRIEVED OFFICIAL KNOWLEDGE CONTEXT:\n"
        f"{formatted_context}\n"
        f"USER QUESTION:\n{message}\n\n"
        f"Instructions: Answer the user's question in {lang_name} adhering strictly to the system rules above."
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


