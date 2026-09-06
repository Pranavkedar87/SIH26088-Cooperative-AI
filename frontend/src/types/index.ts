// ── Language support ──────────────────────────────────────────────────────────

export type LanguageCode =
  | "hi"
  | "en"
  | "mr"
  | "gu"
  | "bn"
  | "ta"
  | "te"
  | "kn"
  | "ml"
  | "pa"
  | "or"
  | "as"
  | "ur"
  | "sa"
  | "ks"
  | "kok"
  | "mai"
  | "mni"
  | "ne"
  | "brx"
  | "sat"
  | "sd";

export interface Language {
  code: LanguageCode;
  label: string;
  nativeLabel: string;
}

export const LANGUAGES: Language[] = [
  { code: "hi", label: "Hindi", nativeLabel: "हिंदी" },
  { code: "en", label: "English", nativeLabel: "English" },
  { code: "mr", label: "Marathi", nativeLabel: "मराठी" },
  { code: "gu", label: "Gujarati", nativeLabel: "ગુજરાતી" },
  { code: "bn", label: "Bengali", nativeLabel: "বাংলা" },
  { code: "ta", label: "Tamil", nativeLabel: "தமிழ்" },
  { code: "te", label: "Telugu", nativeLabel: "తెలుగు" },
  { code: "kn", label: "Kannada", nativeLabel: "ಕನ್ನಡ" },
  { code: "ml", label: "Malayalam", nativeLabel: "മലയാളം" },
  { code: "pa", label: "Punjabi", nativeLabel: "ਪੰਜਾਬੀ" },
  { code: "or", label: "Odia", nativeLabel: "ଓଡ଼ିଆ" },
  { code: "as", label: "Assamese", nativeLabel: "অসমীয়া" },
  { code: "ur", label: "Urdu", nativeLabel: "اردو" },
  { code: "sa", label: "Sanskrit", nativeLabel: "संस्कृतम्" },
  { code: "ks", label: "Kashmiri", nativeLabel: "کٲشُر" },
  { code: "kok", label: "Konkani", nativeLabel: "कोंकणी" },
  { code: "mai", label: "Maithili", nativeLabel: "मैथिली" },
  { code: "mni", label: "Manipuri", nativeLabel: "मৈতৈলোন্" },
  { code: "ne", label: "Nepali", nativeLabel: "नेपाली" },
  { code: "brx", label: "Bodo", nativeLabel: "बड़ो" },
  { code: "sat", label: "Santali", nativeLabel: "ᱥᱟᱱᱛᱟᱲᱤ" },
  { code: "sd", label: "Sindhi", nativeLabel: "سنڌي" },
];

// ── Application Navigation Tabs ───────────────────────────────────────────────

export type AppTab = "home" | "ask" | "services" | "grievance" | "history";

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
    labelHi: "उप-नियम",
    labelMr: "उपविधी",
    prompt: "Explain the standard by-laws for a cooperative society.",
  },
  {
    id: "schemes",
    label: "Government Schemes",
    labelHi: "सरकारी योजनाएं",
    labelMr: "सरकारी योजना",
    prompt: "What government schemes are available for cooperative societies?",
  },
  {
    id: "pacs",
    label: "PACS Services",
    labelHi: "पैक्स (PACS)",
    labelMr: "पॅक्स (PACS)",
    prompt: "How do Primary Agricultural Credit Societies (PACS) work?",
  },
  {
    id: "pmfby",
    label: "PMFBY Crop Insurance",
    labelHi: "पीएमएफबीवाई",
    labelMr: "पीएमएफबीवाय (PMFBY)",
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
    label: "Grievance Redressal",
    labelHi: "शिकायत निवारण",
    labelMr: "तक्रार निवारण",
    prompt: "How do I file a grievance against a cooperative society?",
  },
];

// ── Chat & Sources ────────────────────────────────────────────────────────────

export interface SourceItem {
  title: string;
  source_name?: string | null;
  source_url?: string | null;
  document_id?: string | null;
}

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  spoken_answer?: string;
  timestamp: Date;
  language: LanguageCode;
  sources?: SourceItem[];
  intent?: string;
  answer_focus?: string;
}

// ── API Contracts ─────────────────────────────────────────────────────────────

export interface QueryRequest {
  message: string;
  language: LanguageCode;
  session_id?: string | null;
  response_mode?: "text" | "voice";
}

export interface QueryResponse {
  answer: string;
  display_answer?: string;
  spoken_answer?: string;
  language: LanguageCode;
  intent: string;
  answer_focus?: string;
  source: string | null;
  sources?: SourceItem[];
  next_action: string | null;
  session_id?: string | null;
  conversation_id?: string | null;
}

// ── Voice / Speech ───────────────────────────────────────────────────────────

export type STTStatus = "idle" | "listening" | "processing" | "error" | "unsupported";

export type VoiceState =
  | "IDLE"
  | "LISTENING"
  | "PROCESSING"
  | "THINKING"
  | "SPEAKING"
  | "FOLLOW_UP_LISTENING"
  | "ERROR";

// ── History & Guidance Items ─────────────────────────────────────────────────

export interface HistoryItem {
  id: string;
  type: "query" | "grievance" | "guided";
  title: string;
  subtitle: string;
  timestamp: string;
  language: LanguageCode;
  details?: string;
}
