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
    "title": "<Short clear domain title answering the user question in target language>",
    "summary": "<1-2 sentence direct summary answer to the user question in target language>",
    "what_should_i_do_now": [
      {
        "title": "<Question-Specific Action Step Title in target language>",
        "content": "<Question-Specific Action Procedure/Content in target language>"
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


INTENT_FALLBACKS: dict[str, dict[str, str]] = {
    "PMFBY": {
        "en": (
            "If your crop has suffered damage due to unseasonal rain, inundation, or natural calamity under PMFBY, "
            "it is mandatory to intimate the insurance company, bank, or local Agriculture Officer within 72 hours. "
            "Please keep your 7/12 land extract, Aadhaar card, and bank passbook ready."
        ),
        "hi": (
            "PMFBY फसल बीमा के तहत यदि आपकी फसल (जैसे सोयाबीन, कपास, धान) प्राकृतिक आपदा या अत्यधिक बारिश से खराब हुई है, "
            "तो 72 घंटे के भीतर बीमा कंपनी, ऐप (Crop Insurance App) या स्थानीय कृषि अधिकारी को सूचित करना अनिवार्य है। "
            "अपना 7/12 खसरा खतौनी, आधार कार्ड और बैंक पासबुक तैयार रखें।"
        ),
        "mr": (
            "PMFBY पीक विम्याअंतर्गत अवेळी पाऊस किंवा नैसर्गिक आपत्तीमुळे पिकाचे नुकसान झाल्यास, "
            "७२ तासांच्या आत विमा कंपनी, PMFBY ॲप किंवा स्थानिक कृषी अधिकाऱ्याकडे तक्रार नोंदवणे बंधनकारक आहे. "
            "आपला ७/१२ उतारा, आधार कार्ड आणि बँक पासबुक तयार ठेवा."
        ),
    },
    "PACS_SERVICE": {
        "en": (
            "Primary Agricultural Credit Societies (PACS) provide short-term crop loans, fertilizers, seeds, and storage support to farmers. "
            "To apply for benefits or membership, submit your 7/12 land extract and Aadhaar card to your local PACS Secretary."
        ),
        "hi": (
            "प्राथमिक कृषि साख समितियों (PACS) के माध्यम से किसानों को अल्पकालिक फसल ऋण, उर्वरक और बीज उपलब्ध कराए जाते हैं। "
            "सदस्यता या ऋण के लिए अपने 7/12 खसरा रिकॉर्ड और आधार कार्ड के साथ स्थानीय PACS सचिव से संपर्क करें।"
        ),
        "mr": (
            "प्राथमिक कृषी पतसंस्था (PACS) मार्फत शेतकऱ्यांना अल्पमुदत पीक कर्ज, खते व बियाणे पुरवले जातात. "
            "सभासदत्व किंवा कर्जासाठी आपल्या ७/१२ उतारा व आधार कार्डसह स्थानिक PACS सचिवांशी संपर्क साधा."
        ),
    },
    "GRIEVANCE": {
        "en": (
            "For disputes, unfair decisions, or delay in cooperative society services, you can file an official grievance with the District Deputy Registrar (DDR) or local Cooperative Officer. Keep your society receipts and written application ready."
        ),
        "hi": (
            "सहकारी समिति या संस्था के विवाद या शिकायत के लिए आप जिला उप-निबंधक (DDR) या सहकारी अधिकारी के पास लिखित शिकायत दर्ज करा सकते हैं। अपने दस्तावेज और आवेदन तैयार रखें।"
        ),
        "mr": (
            "सहकारी संस्थेतील तक्रार किंवा वादासाठी तुम्ही जिल्हा उपनिबंधक (DDR) किंवा सहकार अधिकाऱ्याकडे लेखी तक्रार नोंदवू शकता. अर्जाची प्रत व पावती सोबत ठेवा."
        ),
    },
    "TRACTOR_PURCHASE": {
        "en": (
            "Government subsidy schemes for agricultural equipment (such as tractors) exist under the Sub-Mission on Agricultural Mechanization (SMAM) and state agriculture department portals. Eligibility ranges from 40% to 50% depending on farmer category."
        ),
        "hi": (
            "कृषि उपकरणों (जैसे ट्रैक्टर) के लिए 'कृषि मशीनीकरण पर उप-मिशन' (SMAM) और राज्य कृषि विभाग के पोर्टलों के तहत 40% से 50% तक सब्सिडी सहायता योजनाएं उपलब्ध हैं।"
        ),
        "mr": (
            "ट्रॅक्टर आणि कृषी अवजारांसाठी 'कृषी यांत्रिकीकरण उप-अभियान' (SMAM) आणि राज्य कृषी विभागाच्या योजनांतर्गत ४०% ते ५०% अनुदान उपलब्ध आहे."
        ),
    },
    "MINISTRY_SCHEME": {
        "en": (
            "Government subsidy schemes for agricultural equipment (such as tractors) exist under the Sub-Mission on Agricultural Mechanization (SMAM) and state agriculture department portals. Eligibility ranges from 40% to 50% depending on farmer category."
        ),
        "hi": (
            "कृषि उपकरणों (जैसे ट्रैक्टर) के लिए 'कृषि मशीनीकरण पर उप-मिशन' (SMAM) और राज्य कृषि विभाग के पोर्टलों के तहत 40% से 50% तक सब्सिडी सहायता योजनाएं उपलब्ध हैं।"
        ),
        "mr": (
            "ट्रॅक्टर आणि कृषी अवजारांसाठी 'कृषी यांत्रिकीकरण उप-अभियान' (SMAM) आणि राज्य कृषी विभागाच्या योजनांतर्गत ४०% ते ५०% अनुदान उपलब्ध आहे."
        ),
    },
    "DEFAULT": {
        "en": (
            "For guidance on cooperative laws, agricultural schemes, and PACS services, please verify with your local District Agriculture Office, PACS center, or official government portal."
        ),
        "hi": (
            "सहकारी नियमों, सरकारी योजनाओं और PACS सेवाओं के संबंध में अधिकृत जानकारी के लिए कृपया निकटतम कृषि कार्यालय, PACS केंद्र या सरकारी पोर्टल से संपर्क करें।"
        ),
        "mr": (
            "सहकारी नियम, शासकीय योजना व PACS सेवांच्या अधिकृत माहितीसाठी कृपया आपल्या स्थानिक कृषी कार्यालय, PACS केंद्र किंवा शासकीय पोर्टलशी संपर्क साधा."
        ),
    },
}

NO_KNOWLEDGE_FALLBACK = INTENT_FALLBACKS["DEFAULT"]
NO_KNOWLEDGE_FALLBACK_WITH_STATE = INTENT_FALLBACKS["DEFAULT"]

def get_intent_fallback(intent: str, language: str = "mr") -> str:
    intent_key = (intent or "").upper()
    fallback_dict = INTENT_FALLBACKS.get(intent_key) or INTENT_FALLBACKS.get("DEFAULT")
    lang_code = language.lower() if language in ["en", "hi", "mr"] else "mr"
    return fallback_dict.get(lang_code) or fallback_dict["en"]


