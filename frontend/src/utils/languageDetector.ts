import type { LanguageCode } from "../types";

/**
 * Detect language code (mr, hi, en, ta, te, kn, gu, bn, pa, ml) from transcript text.
 * Falls back to active UI language if detection is ambiguous.
 * NEVER hardcodes to English unless text is clearly English.
 */
export function detectLanguageFromText(
  text: string,
  fallbackLang: LanguageCode = "mr"
): LanguageCode {
  if (!text || !text.trim()) {
    return fallbackLang;
  }

  const str = text.trim();

  // 1. Script checks (Unicode Ranges)
  const hasDevanagari = /[\u0900-\u097F]/.test(str);
  const hasTamil = /[\u0B80-\u0BFF]/.test(str);
  const hasTelugu = /[\u0C00-\u0C7F]/.test(str);
  const hasKannada = /[\u0C80-\u0CFF]/.test(str);
  const hasGujarati = /[\u0A80-\u0AFF]/.test(str);
  const hasBengali = /[\u0980-\u09FF]/.test(str);
  const hasPunjabi = /[\u0A00-\u0A7F]/.test(str);
  const hasMalayalam = /[\u0D00-\u0D7F]/.test(str);

  if (hasTamil) return "ta" as LanguageCode;
  if (hasTelugu) return "te" as LanguageCode;
  if (hasKannada) return "kn" as LanguageCode;
  if (hasGujarati) return "gu" as LanguageCode;
  if (hasBengali) return "bn" as LanguageCode;
  if (hasPunjabi) return "pa" as LanguageCode;
  if (hasMalayalam) return "ml" as LanguageCode;

  // 2. Devanagari script: Distinguish Marathi vs Hindi
  if (hasDevanagari) {
    const lower = str.toLowerCase();
    
    // Marathi specific words & suffixes
    const marathiKeywords = [
      "आहे", "आहेत", "आलो", "झाले", "झाला", "झाली", "माझ्या", "माझा", "माझी",
      "काय", "करू", "मदत", "मला", "नाही", "पिकाचे", "पिक", "पाहिजे", "कुठे",
      "केव्हा", "कसा", "कशी", "कोणी", "सोसायटी", "पॅक्स", "तक्रार", "नुकसान",
      "माहिती", "पाहा", "द्या", "सांगा", "मिळेल", "करावे"
    ];

    // Hindi specific words
    const hindiKeywords = [
      "है", "हूँ", "हैं", "क्या", "हुआ", "हुई", "मेरा", "मेरी", "मेरे",
      "मुझे", "नहीं", "फसल", "चाहिए", "कहाँ", "कब", "कैसे", "किसने", "पैक्स",
      "शिकायत", "मदद", "बताएं", "मिलेगा", "करना"
    ];

    let mrScore = 0;
    let hiScore = 0;

    marathiKeywords.forEach((kw) => {
      if (lower.includes(kw)) mrScore++;
    });

    hindiKeywords.forEach((kw) => {
      if (lower.includes(kw)) hiScore++;
    });

    if (mrScore > hiScore) return "mr";
    if (hiScore > mrScore) return "hi";

    // If score tied, align with user UI preference if it's Devanagari (mr or hi)
    if (fallbackLang === "hi" || fallbackLang === "mr") {
      return fallbackLang;
    }
    return "mr"; // Default Devanagari to Marathi for SahkaarSetu
  }

  // 3. Latin script (Transliterated Hinglish / Marathlish or English)
  const lowerStr = str.toLowerCase();

  const marathlishKW = [
    "majhya", "majha", "majhi", "kaay", "jhale", "madat", "pikasathi",
    "kute", "kadhi", "pahije", "nuksan", "takrar", "karaye", "karaycha"
  ];
  if (marathlishKW.some((kw) => lowerStr.includes(kw))) {
    return "mr";
  }

  const hinglishKW = [
    "mera", "meri", "mere", "kya", "hua", "chahiye", "kaise", "kahan",
    "shikayat", "batao", "kaise kare"
  ];
  if (hinglishKW.some((kw) => lowerStr.includes(kw))) {
    return "hi";
  }

  // Pure English text default to 'en'
  return "en";
}
