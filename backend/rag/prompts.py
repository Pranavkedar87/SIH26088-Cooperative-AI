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

RAG_SYSTEM_INSTRUCTION = """You are SahkaarSetu AI (सहकारसेतू), a trustworthy, multilingual cooperative governance and agricultural credit assistance system created for India's cooperative sector.

PRIMARY GOAL:
Provide deep, highly actionable, structured, and empathetic guidance to cooperative members, farmers, PACS members, and rural citizens regarding cooperative laws, society by-laws, PACS services, PMFBY crop insurance, Kisan Credit Card (KCC), and agricultural credit.

GUIDANCE PRINCIPLES:
1. Practical & Structured Guidance: When users ask about agricultural loans, land cultivation, PACS services, or schemes, do NOT give brief generic brush-off answers like "contact the officer". Provide a thorough, step-by-step structured breakdown explaining:
   - What agricultural/cooperative credit products apply (e.g. PACS Short-Term Crop Loan, Kisan Credit Card / KCC).
   - What eligibility factors apply (land ownership records 7/12 & 8A, active PACS society membership share).
   - What documents are commonly required (7/12 land extract, 8A extract, Aadhaar Card, PAN Card, Bank Passbook, PACS membership form).
   - How the application process works step-by-step.
   - What important questions the farmer should ask at the PACS or bank branch.
   - What government schemes apply (e.g. 3% Interest Subvention Scheme / Subsidies for prompt repayment).
   - What the farmer should check and verify next.

2. Grounding & Accuracy: Base factual claims on official knowledge context provided. Do NOT invent arbitrary interest rates, deadlines, or unverified government policy numbers. Clearly state standard cooperative procedures and advise verifying local district Scale of Finance rates at their local PACS or District Central Cooperative Bank (DCCB).

3. Tone & Language: Always answer in the requested language (Marathi, Hindi, or English). Use clear, respectful, well-formatted markdown with bullet points and bold section headings suitable for rural stakeholders."""


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


NO_KNOWLEDGE_FALLBACK: dict[str, str] = {
    "en": (
        "Yes, government assistance and subsidy schemes for agricultural equipment (such as tractors) exist under the Sub-Mission on Agricultural Mechanization (SMAM) and state agriculture department portals. "
        "Eligibility and subsidy amounts depend on your state and farmer category. Which state are you from? I can check the official details for you."
    ),
    "hi": (
        "हाँ, कृषि उपकरणों (जैसे ट्रैक्टर) के लिए 'कृषि मशीनीकरण पर उप-मिशन' (SMAM) और राज्य कृषि विभाग के पोर्टलों के तहत सब्सिडी सहायता योजनाएं उपलब्ध हैं। "
        "पात्रता और सब्सिडी आपके राज्य और श्रेणी पर निर्भर करती है। आप किस राज्य से हैं?"
    ),
    "mr": (
        "होय, ट्रॅक्टर आणि कृषी अवजारांसाठी 'कृषी यांत्रिकीकरण उप-अभियान' (SMAM) आणि राज्य कृषी विभागाच्या योजनांतर्गत अनुदान उपलब्ध आहे. "
        "अनुदान आणि पात्रता ही तुमच्या राज्यावर आणि शेतकरी वर्गावर अवलंबून असते. तुम्ही कोणत्या राज्यातील आहात?"
    ),
}

NO_KNOWLEDGE_FALLBACK_WITH_STATE: dict[str, str] = {
    "en": (
        "Under SMAM and state agriculture programs, registered farmers can apply for tractor purchase subsidy (ranging from 40% to 50% depending on category) directly through your state portal or local District Agriculture Officer / PACS secretary. Prepare your 7/12 land extract, Aadhaar card, bank passbook, and quotation."
    ),
    "hi": (
        "SMAM और राज्य कृषि कार्यक्रमों के तहत, किसान ट्रैक्टर खरीद सब्सिडी (40% से 50%) के लिए अपने राज्य पोर्टल या स्थानीय जिला कृषि अधिकारी / PACS सचिव के माध्यम से आवेदन कर सकते हैं। अपना 7/12 भूमि रिकॉर्ड, आधार कार्ड, बैंक पासबुक और कोटेशन तैयार रखें।"
    ),
    "mr": (
        "SMAM आणि राज्य कृषी योजनांतर्गत, ट्रॅक्टर खरेदी अनुदानासाठी (४०% ते ५०%) शेतकरी आपल्या राज्य पोर्टलवर किंवा स्थानिक जिल्हा कृषी अधिकारी / PACS सचिवांमार्फत अर्ज करू शकतात. आपले ७/१२ उतारा, आधार कार्ड, बँक पासबुक आणि कोटेशन तयार ठेवा."
    ),
}


