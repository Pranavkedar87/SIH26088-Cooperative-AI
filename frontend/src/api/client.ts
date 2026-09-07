/**
 * API client — all backend communication goes through here.
 *
 * Guaranteed resilience:
 * - Retries cold-starting backends automatically.
 * - Handles Safari / iOS "Load failed" & "Failed to fetch" errors gracefully.
 * - Synthesizes grounded fallback guidance if backend is completely offline.
 */
import type { QueryRequest, QueryResponse } from "../types";

const DEFAULT_PROD_URL = "https://sih26088-cooperative-ai.onrender.com";
const DEFAULT_DEV_URL = "http://localhost:8000";

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.PROD ? DEFAULT_PROD_URL : DEFAULT_DEV_URL);

// ── Health ────────────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<{ status: string }> {
  try {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) throw new Error("Backend health check failed");
    return res.json();
  } catch {
    return { status: "offline_fallback" };
  }
}

// ── Standalone Knowledge Fallback Generator for Offline/Cold-Start ───────────

function generateFallbackResponse(request: QueryRequest): QueryResponse {
  const msg = request.message.toLowerCase();
  const lang = request.language || "en";

  // 1. General Knowledge & Prime Minister Query
  if (msg.includes("prime minister") || msg.includes("narendra modi") || msg.includes("pm of india") || msg.includes("minister")) {
    const ans =
      lang === "hi"
        ? "भारत के वर्तमान प्रधानमंत्री नरेंद्र मोदी हैं। क्या आप उनकी किसी कृषि या सरकारी योजना के बारे में जानना चाहते हैं?"
        : lang === "mr"
        ? "भारताचे सध्याचे पंतप्रधान नरेंद्र मोदी आहेत. तुम्हाला त्यांच्या एखाद्या शासकीय योजनेबद्दल माहिती हवी आहे का?"
        : "The Prime Minister of India is Narendra Modi. Would you like to know more about government schemes or agricultural initiatives?";
    return {
      answer: ans,
      display_answer: ans,
      spoken_answer: ans,
      language: lang,
      intent: "GENERAL_KNOWLEDGE",
      source: "Official Indian Government Information",
      sources: [
        {
          title: "Prime Minister's Office (PMO India)",
          source_name: "pmoffice.gov.in",
          source_url: "https://www.pmindia.gov.in",
        },
      ],
      next_action: null,
    };
  }

  // 2. Greetings & Conversational Inputs
  if (msg.includes("hello") || msg.includes("namaskar") || msg.includes("namaste") || msg.includes("hi") || msg.includes("hey")) {
    const ans =
      lang === "hi"
        ? "नमस्ते! मैं सहकारसेतू वॉइस असिस्टेंट हूँ। आप मुझसे फसल बीमा, PACS ऋण, सहकारी नियम या सरकारी योजनाओं के बारे में पूछ सकते हैं।"
        : lang === "mr"
        ? "नमस्कार! मी सहकारसेतू व्हॉइस असिस्टंट आहे. पीक विमा, PACS कर्ज, सहकारी कायदे किंवा शासकीय योजनांबद्दल तुम्ही मला विचारू शकता."
        : "Hello! I am SahkaarSetu Voice Assistant. How can I help you with crop insurance, PACS loans, cooperative rules, or government schemes today?";
    return {
      answer: ans,
      display_answer: ans,
      spoken_answer: ans,
      language: lang,
      intent: "CASUAL_GREETING",
      source: "SahkaarSetu Voice Assistant",
      sources: [],
      next_action: null,
    };
  }

  // 3. Agricultural Loans & Land Queries
  if (msg.includes("loan") || msg.includes("land") || msg.includes("acre") || msg.includes("कर्ज") || msg.includes("ऋण") || msg.includes("जमीन") || msg.includes("एकर")) {
    const ans =
      lang === "hi"
        ? "हाँ, आप अपनी भूमि और फसल के आधार पर किसान क्रेडिट कार्ड (KCC) या PACS फसल ऋण के लिए आवेदन कर सकते हैं। अधिक जानकारी के लिए 7/12 रिकॉर्ड के साथ स्थानीय PACS सचिव से संपर्क करें।"
        : lang === "mr"
        ? "होय, तुमच्या जमिनीच्या ७/१२ उताऱ्यानुसार तुम्ही किसान क्रेडिट कार्ड (KCC) किंवा PACS पीक कर्जासाठी अर्ज करू शकता. अधिक माहितीसाठी स्थानिक PACS सचिवांशी संपर्क साधा."
        : "Yes, you can explore agricultural credit options such as a crop loan or Kisan Credit Card (KCC). Eligibility depends on your crop, land records, and local PACS rules.";
    return {
      answer: ans,
      display_answer: ans,
      spoken_answer: ans,
      language: lang,
      intent: "AGRICULTURAL_SUPPORT",
      source: "NABARD & PACS Credit Guidelines",
      sources: [
        {
          title: "Kisan Credit Card (KCC) Scheme Guidelines",
          source_name: "Ministry of Agriculture",
          source_url: "https://agri.gov.in",
        },
      ],
      next_action: null,
    };
  }

  // 4. PMFBY Crop Insurance Query
  if (
    msg.includes("pmfby") ||
    msg.includes("crop") ||
    msg.includes("insurance") ||
    msg.includes("पिक") ||
    msg.includes("फसल") ||
    msg.includes("विमा") ||
    msg.includes("बीमा") ||
    msg.includes("नुकसान") ||
    msg.includes("सोयाबीन") ||
    msg.includes("soyabean") ||
    msg.includes("soybean") ||
    msg.includes("खराब") ||
    msg.includes("ख़राब")
  ) {
    const ans =
      lang === "hi"
        ? "यदि आपकी फसल प्राकृतिक आपदा से प्रभावित हुई है, तो 72 घंटे के भीतर PMFBY ऐप या कृषि अधिकारी को सूचित करें। अपना 7/12 खसरा रिकॉर्ड और बैंक पासबुक तैयार रखें।"
        : lang === "mr"
        ? "अतिवृष्टी किंवा आपत्तीमुळे पिकाचे नुकसान झाल्यास ७२ तासांच्या आत PMFBY ॲप किंवा कृषी अधिकाऱ्याकडे तक्रार नोंदवणे बंधनकारक आहे. ७/१२ उतारा व आधार कार्ड सोबत ठेवा."
        : "If your crop suffered damage, report it within 72 hours via the PMFBY app or to your local agriculture officer. Keep your 7/12 land extract and bank passbook ready.";
    return {
      answer: ans,
      display_answer: ans,
      spoken_answer: ans,
      language: lang,
      intent: "PMFBY",
      source: "PMFBY Guidelines",
      sources: [
        {
          title: "PMFBY Operational Guidelines",
          source_name: "Ministry of Agriculture",
          source_url: "https://pmfby.gov.in",
        },
      ],
      next_action: null,
    };
  }

  // 5. Default Neutral Network/Timeout Assistance Fallback
  const defaultAns =
    lang === "hi"
      ? "मैं अभी सहायता सेवा से संपर्क नहीं कर पा रहा हूँ। कृपया कुछ समय बाद पुनः प्रयास करें।"
      : lang === "mr"
      ? "मी सध्या सहाय्य सेवेशी संपर्क साधू शकत नाही. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा."
      : "I'm unable to reach the assistance service right now. Please try again shortly.";

  return {
    answer: defaultAns,
    display_answer: defaultAns,
    spoken_answer: defaultAns,
    language: lang,
    intent: "COOPERATIVE_GENERAL",
    source: "SahkaarSetu Network Assistance",
    sources: [],
    next_action: null,
  };
}

// ── Send Query with Auto-Retry & Standalone Fallback ─────────────────────────

export async function sendQuery(request: QueryRequest): Promise<QueryResponse> {
  let attempts = 0;
  const maxAttempts = 2;

  while (attempts < maxAttempts) {
    try {
      attempts++;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 12000); // 12s timeout per request

      const res = await fetch(`${BASE_URL}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (res.ok) {
        return await res.json();
      }
    } catch (err) {
      console.warn(`Query attempt ${attempts} failed:`, err);
      if (attempts < maxAttempts) {
        await new Promise((r) => setTimeout(r, 1000)); // wait 1s before retry
      }
    }
  }

  // If backend is cold-starting or offline, return clean grounded standalone fallback
  console.info("Using SahkaarSetu standalone knowledge fallback for query resilience.");
  return generateFallbackResponse(request);
}

// ── Send Voice Query (Targeting /api/voice/query) ────────────────────────────

export async function sendVoiceQuery(request: QueryRequest): Promise<QueryResponse> {
  let attempts = 0;
  const maxAttempts = 2;

  const payload = {
    transcript: request.message,
    query: request.message,
    language: request.language,
    session_id: request.session_id,
    response_mode: request.response_mode || "voice",
  };

  while (attempts < maxAttempts) {
    try {
      attempts++;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 12000);

      const res = await fetch(`${BASE_URL}/api/voice/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (res.ok) {
        return await res.json();
      }
    } catch (err) {
      console.warn(`Voice query attempt ${attempts} failed:`, err);
      if (attempts < maxAttempts) {
        await new Promise((r) => setTimeout(r, 1000));
      }
    }
  }

  console.info("Falling back to sendQuery for voice resilience.");
  return sendQuery(request);
}

// ── Server-Side STT Audio Transcription ──────────────────────────────────────

export interface TranscribeResponseData {
  transcript: string;
  language: string;
  confidence: number;
  provider: string;
  latency_ms?: number;
}

export function wakeUpBackend(): void {
  try {
    fetch(`${BASE_URL}/health`, { method: "GET" }).catch(() => {
      // Non-blocking background health check to wake up cold backend
    });
  } catch {
    // Ignore
  }
}

export async function transcribeAudio(
  audioBlob: Blob,
  language: string,
  sessionId?: string
): Promise<TranscribeResponseData> {
  const typeStr = (audioBlob.type || "").toLowerCase();
  const isAppleDevice =
    typeof navigator !== "undefined" &&
    /iPad|iPhone|iPod|Macintosh/.test(navigator.userAgent);

  let filename = "speech.webm";
  if (
    typeStr.includes("mp4") ||
    typeStr.includes("aac") ||
    typeStr.includes("m4a") ||
    (isAppleDevice && !typeStr.includes("webm"))
  ) {
    filename = "speech.mp4";
  } else if (typeStr.includes("wav")) {
    filename = "speech.wav";
  } else if (typeStr.includes("ogg")) {
    filename = "speech.ogg";
  }

  const formData = new FormData();
  formData.append("audio", audioBlob, filename);
  formData.append("language", language);
  if (sessionId) {
    formData.append("session_id", sessionId);
  }

  const startTime = performance.now();
  console.info(`[STT] STT_REQUEST_STARTED provider=groq_whisper lang=${language} size=${audioBlob.size} bytes mime=${audioBlob.type} filename=${filename}`);

  const maxAttempts = 2;
  let attempts = 0;

  while (attempts < maxAttempts) {
    try {
      attempts++;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 25000); // 25s timeout for Render cold-start

      const res = await fetch(`${BASE_URL}/api/voice/transcribe`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (res.ok) {
        const data: TranscribeResponseData = await res.json();
        const elapsed = Math.round(performance.now() - startTime);
        console.info(
          `[STT] STT_RESPONSE_RECEIVED latency=${elapsed}ms provider=${data.provider} transcript="${data.transcript}"`
        );
        return data;
      }

      const errData = await res.json().catch(() => ({ detail: "STT transcription failed" }));
      console.warn(`[STT] STT_RESPONSE_FAILED attempt ${attempts} status=${res.status} detail=${errData.detail}`);
    } catch (err) {
      console.warn(`[STT] Audio transcription attempt ${attempts} failed:`, err);
      if (attempts < maxAttempts) {
        await new Promise((r) => setTimeout(r, 1500)); // wait 1.5s before retry
      }
    }
  }

  throw new Error("Audio transcription timed out or backend is offline");
}

