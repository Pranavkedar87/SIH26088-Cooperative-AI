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

  // 1. Casual Greetings Only
  if (msg.includes("hello") || msg.includes("namaskar") || msg.includes("namaste") || msg.includes("hi") || msg.includes("hey")) {
    const ans =
      lang === "hi"
        ? "नमस्ते! मैं सहकारसेतू वॉइस असिस्टेंट हूँ। मैं आपकी किस प्रकार सहायता कर सकता हूँ?"
        : lang === "mr"
        ? "नमस्कार! मी सहकारसेतू व्हॉइस असिस्टंट आहे. मी तुम्हाला कशी मदत करू शकतो?"
        : "Hello! I am SahkaarSetu Voice Assistant. How can I help you today?";
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

  // 2. Default Neutral Network/Timeout Assistance Fallback (No Hardcoded Facts)
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

