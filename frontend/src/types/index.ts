// ── Language support ──────────────────────────────────────────────────────────

export type LanguageCode = "en" | "hi" | "mr";

export interface Language {
  code: LanguageCode;
  label: string;
  nativeLabel: string;
}

export const LANGUAGES: Language[] = [
  { code: "en", label: "English", nativeLabel: "English" },
  { code: "hi", label: "Hindi", nativeLabel: "हिंदी" },
  { code: "mr", label: "Marathi", nativeLabel: "मराठी" },
];

// ── Quick topics ──────────────────────────────────────────────────────────────

export interface QuickTopic {
  id: string;
  label: string;
  labelHi: string;
  labelMr: string;
  prompt: string;
}

export const QUICK_TOPICS: QuickTopic[] = [
  {
    id: "cooperative_laws",
    label: "Cooperative Laws",
    labelHi: "सहकारी कानून",
    labelMr: "सहकारी कायदे",
    prompt: "What are the key provisions of the Maharashtra Cooperative Societies Act?",
  },
  {
    id: "by_laws",
    label: "By-laws",
    labelHi: "उपनियम",
    labelMr: "उपविधी",
    prompt: "Explain the standard by-laws for a cooperative society.",
  },
  {
    id: "schemes",
    label: "Schemes",
    labelHi: "योजनाएं",
    labelMr: "योजना",
    prompt: "What government schemes are available for cooperative societies?",
  },
  {
    id: "pacs",
    label: "PACS",
    labelHi: "पैक्स",
    labelMr: "पॅक्स",
    prompt: "How do Primary Agricultural Credit Societies (PACS) work?",
  },
  {
    id: "pmfby",
    label: "PMFBY",
    labelHi: "पीएमएफबीवाई",
    labelMr: "पीएमएफबीवाय",
    prompt: "Explain the Pradhan Mantri Fasal Bima Yojana (PMFBY) scheme.",
  },
  {
    id: "financial_literacy",
    label: "Financial Literacy",
    labelHi: "वित्तीय साक्षरता",
    labelMr: "आर्थिक साक्षरता",
    prompt: "Give me basic financial literacy tips for cooperative members.",
  },
  {
    id: "grievance",
    label: "Grievance",
    labelHi: "शिकायत",
    labelMr: "तक्रार",
    prompt: "How do I file a grievance against a cooperative society?",
  },
];

// ── Chat ──────────────────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  language: LanguageCode;
}

// ── API ───────────────────────────────────────────────────────────────────────

export interface QueryRequest {
  message: string;
  language: LanguageCode;
}

export interface QueryResponse {
  answer: string;
  language: LanguageCode;
  intent: string;
  source: string | null;
  next_action: string | null;
}
