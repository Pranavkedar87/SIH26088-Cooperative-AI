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
  const lang = request.language || "mr";
  const isVoice = request.response_mode === "voice";

  // PMFBY Crop Insurance Query
  if (
    msg.includes("pmfby") ||
    msg.includes("crop") ||
    msg.includes("insurance") ||
    msg.includes("पिक") ||
    msg.includes("विमा") ||
    msg.includes("नुकसान") ||
    msg.includes("खरीप") ||
    msg.includes("रब्बी") ||
    msg.includes("72")
  ) {
    if (isVoice) {
      const voiceAns =
        lang === "hi"
          ? "आपकी फसल का नुकसान हुआ है, तो 72 घंटे के भीतर PMFBY ऐप या कृषि अधिकारी को सूचित करें। आधार कार्ड और 7/12 पासबुक तैयार रखें।"
          : lang === "en"
          ? "If your crop suffered damage, report it within 72 hours via the PMFBY app or to your local agriculture officer. Keep land documents ready."
          : "तुमच्या पिकाचे नुकसान झाले असल्यास, ७२ तासांच्या आत PMFBY ॲप किंवा कृषी अधिकाऱ्याकडे तक्रार नोंदवा. ७/१२ उतारा व आधार कार्ड सोबत ठेवा.";
      return {
        answer: voiceAns,
        language: lang,
        intent: "PMFBY",
        source: "PMFBY Guidelines",
        sources: [],
        next_action: null,
      };
    }
    if (lang === "hi") {
      return {
        answer: `### 1. फसल क्षति दावा एवं 72 घंटे की समय-सीमा

**PMFBY फसल बीमा दावा प्रक्रिया:** बाढ़, अत्यधिक बारिश या प्राकृतिक आपदा से फसल क्षति होने पर 72 घंटे के भीतर बीमा कंपनी, बैंक या कृषि अधिकारी को सूचित करना अनिवार्य है।

**मुख्य विवरण एवं दरें:**
- **दावा सूचना अवधि:** 72 घंटे (आपदा के बाद)
- **खरीफ प्रीमियम दर:** 2.0% (किसानों का अंशदान)
- **रबी प्रीमियम दर:** 1.5%
- **हेल्पलाइन नंबर:** 14447 / Crop Insurance App

### 2. आधिकारिक क्षति पूर्ति प्रक्रिया

1. **सूचना देना:** 72 घंटे के भीतर PMFBY App, CSC केंद्र या बैंक में क्षति दर्ज कराएं।
2. **आवश्यक दस्तावेज:** 7/12 खसरा खतौनी, बैंक पासबुक, आधार कार्ड एवं क्षति के चित्र।
3. **स्थल निरीक्षण:** कृषि अधिकारी एवं बीमा प्रतिनिधि 5 दिनों के भीतर प्रत्यक्ष सर्वेक्षण करेंगे।

### 3. महत्वपूर्ण सूचना

72 घंटे के बाद दी गई सूचना खारिज की जा सकती है, इसलिए समय पर सूचना दर्ज करें।`,
        language: "hi",
        intent: "PMFBY_CLAIM",
        source: "Ministry of Agriculture & PMFBY Guidelines",
        sources: [
          {
            title: "PMFBY Operational Guidelines",
            source_name: "Ministry of Agriculture & Farmers Welfare",
            source_url: "https://pmfby.gov.in",
          },
        ],
        next_action: null,
      };
    }

    if (lang === "en") {
      return {
        answer: `### 1. Crop Loss Intimation & 72-Hour Claim Window

**PMFBY Claim Reporting:** In case of crop loss due to heavy rain, inundation, or localized calamity, it is mandatory to inform the insurance company within 72 hours.

**Key Facts & Rates:**
- **Intimation Deadline:** 72 hours (post-calamity)
- **Kharif Premium Rate:** 2.0% (farmer contribution)
- **Rabi Premium Rate:** 1.5%
- **Toll-Free Helpline:** 14447 / Crop Insurance App

### 2. Official Step-by-Step Claim Procedure

1. **Submit Intimation:** Intimate loss within 72 hours via PMFBY App, CSC Center, or Bank.
2. **Required Documents:** 7/12 land extract, Aadhaar card, Bank passbook & loss photos.
3. **Field Assessment:** Agriculture Officer & insurance representative survey field within 5 days.

### 3. Important Notice

Delayed intimations beyond 72 hours are liable for rejection. Notify immediately.`,
        language: "en",
        intent: "PMFBY_CLAIM",
        source: "Ministry of Agriculture & PMFBY Guidelines",
        sources: [
          {
            title: "PMFBY Operational Guidelines",
            source_name: "Ministry of Agriculture & Farmers Welfare",
            source_url: "https://pmfby.gov.in",
          },
        ],
        next_action: null,
      };
    }

    // Default Marathi
    return {
      answer: `### 1. विमा संरक्षण आणि ७२ तास तक्रार मुदत

**PMFBY पीक नुकसान भरपाई प्रक्रिया:** अतिवृष्टी, पूर किंवा स्थानिक आपत्तीमुळे पिकाचे नुकसान झाल्यास ७२ तासांच्या आत विमा कंपनी किंवा कृषी विभागाला कळवणे बंधनकारक आहे.

**महत्त्वाचे तपशील व दर:**
- **तक्रार मुदत:** ७२ तास (आपत्तीनंतर)
- **खरीप हप्ता:** २.०% (शेतकऱ्यांचा वाटा)
- **रब्बी हप्ता:** १.५%
- **हेल्पलाईन नंबर:** 14447 / PMFBY Crop Insurance App

### 2. नुकसान भरपाई मिळवण्यासाठी अधिकृत प्रक्रिया

1. **सूचना देणे:** ७२ तासांच्या आत PMFBY ॲप, CSC केंद्र, बँक किंवा कृषी अधिकाऱ्याला कळवणे.
2. **अर्ज व पुरावे:** 7/12 उतारा, बँक पासबुक, आधार कार्ड आणि नुकसानाचे फोटो जमा करणे.
3. **पंचनामा:** कृषी अधिकारी व विमा प्रतिनिधी ५ दिवसांत प्रत्यक्ष पाहणी करतील.

### 3. महत्त्वाच्या सूचना

७२ तासांनंतर नोंदवलेल्या तक्रारी फेटाळल्या जाऊ शकतात, म्हणून तात्काळ सूचना नोंदवा.`,
      language: "mr",
      intent: "PMFBY_CLAIM",
      source: "कृषी विभाग व PMFBY मार्गदर्शक सूचना",
      sources: [
        {
          title: "PMFBY मार्गदर्शक तत्त्वे",
          source_name: "कृषी व शेतकरी कल्याण मंत्रालय",
          source_url: "https://pmfby.gov.in",
        },
      ],
      next_action: null,
    };
  }

  // PACS Query
  if (msg.includes("pacs") || msg.includes("पॅक्स") || msg.includes("सोसायटी")) {
    if (isVoice) {
      const voiceAns =
        lang === "hi"
          ? "पैक्स संस्थाएं किसानों को अल्पकालिक ऋण, खाद और बीज उपलब्ध कराती हैं। आप 7/12 और आधार कार्ड के साथ सदस्य बन सकते हैं।"
          : lang === "en"
          ? "PACS credit societies provide short-term crop loans, fertilizers, and seeds to farmers. You can join with land documents and Aadhaar."
          : "पॅक्स संस्था शेतकऱ्यांना अल्पमुदत पीक कर्ज, खते आणि बियाणे पुरवतात. ७/१२ उतारा आणि आधार कार्ड देऊन तुम्ही सभासद होऊ शकता.";
      return {
        answer: voiceAns,
        language: lang,
        intent: "PACS_SERVICE",
        source: "PACS Guidelines",
        sources: [],
        next_action: null,
      };
    }
    return {
      answer: `### 1. प्राथमिक कृषी पतसंस्था (PACS) सेवा

**PACS सोसायटीची भूमिका:** प्राथमिक कृषी पतसंस्था (PACS) ग्रामीण स्तरावर शेतकऱ्यांना अल्पमुदत पीक कर्ज, खते, बियाणे आणि शेती निविष्ठा पुरवण्याचे महत्त्वाचे काम करतात.

**महत्त्वाचे तपशील:**
- **मुख्य उद्देश:** शेतकऱ्यांना वेळेवर व सवलतीचे कर्ज देणे
- **व्याज सवलत:** वेळेवर परतफेडीवर ३% व्याज परतावा
- **सदस्यत्व पात्रता:** क्षेत्रातील शेतकरी / 7/12धारक

### 2. PACS सेवा व लाभ प्रक्रिया

1. **सभासद अर्ज:** 7/12 उतारा व आधार कार्डसह PACS सचिवांकडे अर्ज सादर करणे.
2. **शेअर भांडवल:** 100/- रुपये भागभांडवल जमा करून अधिकृत सभासदत्व मिळवणे.
3. **पीक कर्ज वाटप:** खरीप व रब्बी हंगामासाठी KCC योजनेअंतर्गत कर्ज मंजूर करणे.`,
      language: lang,
      intent: "PACS_SERVICES",
      source: "महाराष्ट्र राज्य सहकार विभाग व NABARD guidelines",
      sources: [
        {
          title: "PACS Modernization & By-laws",
          source_name: "Ministry of Cooperation",
          source_url: "https://cooperation.gov.in",
        },
      ],
      next_action: null,
    };
  }

  // Default Information Fallback
  return {
    answer: `### 1. अधिकृत सहकार मार्गदर्शन

**सहकार सेतू अधिकृत माहिती:** महाराष्ट्र सहकारी संस्था कायदा १९६० व केंद्र सरकारच्या सहकार मंत्रालयानुसार सर्व सहकारी संस्थांच्या कारभारात पारदर्शकता व सभासद हित जपणे बंधनकारक आहे.

**महत्त्वाचे तपशील:**
- **वार्षिक सभा (AGM):** ३० सप्टेंबरपूर्वी आयोजित करणे आवश्यक
- **लेखापरीक्षण (Audit):** वर्षातून एकदा अधिकृत ऑपरेटरद्वारे अनिवार्य
- **दाद मागण्याचा अधिकार:** DDR उपनिबंधक किंवा सहकार न्यायालय

### 2. पुढील कारवाई

1. **संबंधित कागदपत्रे जमा करा:** अर्ज, पावती व पुरावे तयार ठेवा.
2. **अधिकृत अर्ज सादर करा:** निबंधक / DDR कार्यालयात लिखित तक्रार नोंदवा.`,
    language: lang,
    intent: "COOPERATIVE_GENERAL",
    source: "महाराष्ट्र सहकारी संस्था कायदा १९६० व सहकार नियम",
    sources: [
      {
        title: "MCS Act 1960 Guide",
        source_name: "Cooperative Department Maharashtra",
        source_url: "https://cooperation.maharashtra.gov.in",
      },
    ],
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

