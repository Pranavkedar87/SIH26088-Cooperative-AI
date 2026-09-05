import React, { useEffect, useState } from "react";
import type { LanguageCode, ChatMessage } from "../types";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";
import { useTextToSpeech } from "../hooks/useTextToSpeech";
import { sendQuery } from "../api/client";
import { detectLanguageFromText } from "../utils/languageDetector";
import {
  SahkaarSetuLogo,
  MicIcon,
  PauseIcon,
  SpeakerIcon,
  ArrowRightIcon,
  ShieldCheckIcon,
} from "./Icons";

interface Props {
  language: LanguageCode;
  onClose: () => void;
  onNavigateToChat?: () => void;
}

const INTENT_LABELS: Record<string, Record<string, string>> = {
  CASUAL_GREETING: { mr: "SAHKAARSETU", hi: "SAHKAARSETU", en: "SAHKAARSETU" },
  GREETING: { mr: "SAHKAARSETU", hi: "SAHKAARSETU", en: "SAHKAARSETU" },
  CASUAL_THANKS: { mr: "SAHKAARSETU", hi: "SAHKAARSETU", en: "SAHKAARSETU" },
  CASUAL_IDENTITY: { mr: "SAHKAARSETU", hi: "SAHKAARSETU", en: "SAHKAARSETU" },
  UNCLEAR: { mr: "सामान्य मदत", hi: "सामान्य सहायता", en: "General Assistance" },
  PMFBY: { mr: "पीक विमा (PMFBY)", hi: "फसल बीमा (PMFBY)", en: "PMFBY Crop Insurance" },
  PACS_SERVICE: { mr: "पॅक्स सेवा (PACS)", hi: "पैक्स सेवाएं (PACS)", en: "PACS Services" },
  COOPERATIVE_LAW: { mr: "सहकारी कायदे", hi: "सहकारी कानून", en: "Cooperative Law" },
  COOPERATIVE_BYLAW: { mr: "सहकारी उपनियम", hi: "सहकारी उपनियम", en: "Cooperative By-Laws" },
  MINISTRY_SCHEME: { mr: "सरकारी योजना", hi: "सरकारी योजनाएं", en: "Government Schemes" },
  GRIEVANCE: { mr: "तक्रार निवारण", hi: "शिकायत सहायता", en: "Grievance Assistance" },
  FINANCIAL_LITERACY: { mr: "आर्थिक साक्षरता", hi: "वित्तीय साक्षरता", en: "Financial Literacy" },
  AGRICULTURAL_SUPPORT: { mr: "कृषी सहाय्य", hi: "कृषि सहायता", en: "Agricultural Support" },
  GENERAL_COOPERATIVE: { mr: "सहकारी मार्गदर्शक", hi: "सहकारी मार्गदर्शक", en: "Cooperative Guidance" },
};

const LANG_DISPLAY_NAMES: Record<string, string> = {
  mr: "मराठी",
  hi: "हिंदी",
  en: "English",
  ta: "தமிழ் (Tamil)",
  te: "తెలుగు (Telugu)",
  kn: "ಕನ್ನಡ (Kannada)",
  gu: "ગુજરાતી (Gujarati)",
  bn: "বাংলা (Bengali)",
  pa: "ਪੰਜਾਬੀ (Punjabi)",
  ml: "മലയാളം (Malayalam)",
};

export const VoiceModeView: React.FC<Props> = ({
  language,
  onClose,
  onNavigateToChat,
}) => {
  // Session ID persisted across continuous voice turns in this session
  const [sessionId] = useState<string>(
    () => `voice-session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
  );

  const [activeLang, setActiveLang] = useState<LanguageCode>(language);
  const [userTranscript, setUserTranscript] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [aiResponse, setAiResponse] = useState<ChatMessage | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { speak, isSpeaking, stop: stopSpeaking, unlockAudio } = useTextToSpeech();

  const handleSpeechCaptured = async (text: string) => {
    if (!text || !text.trim() || isProcessing) return;

    const startTime = performance.now();
    const trimmed = text.trim();
    setUserTranscript(trimmed);
    setIsProcessing(true);
    setErrorMsg(null);
    stopSpeaking();
    unlockAudio();

    // 1. Detect language from spoken input
    const detectedLang = detectLanguageFromText(trimmed, activeLang);
    setActiveLang(detectedLang);

    try {
      // 2. Query backend with response_mode = "voice" for fast concise spoken answer
      const response = await sendQuery({
        message: trimmed,
        language: detectedLang,
        session_id: sessionId,
        response_mode: "voice",
      });

      const elapsed = Math.round(performance.now() - startTime);
      console.info(
        `[VOICE_LATENCY] Captured: "${trimmed}" | Detected lang: ${detectedLang} | Intent: ${response.intent} | Time: ${elapsed}ms`
      );

      const assistantMsg: ChatMessage = {
        id: `voice-msg-${Date.now()}`,
        role: "assistant",
        content: response.answer,
        timestamp: new Date(),
        language: response.language || detectedLang,
        sources: response.sources,
        intent: response.intent,
      };

      setAiResponse(assistantMsg);

      // 3. AUTOMATIC VOICE PLAYBACK IN DETECTED LANGUAGE
      const targetLang = response.language || detectedLang;
      speak(assistantMsg.id, response.answer, targetLang);
    } catch (err) {
      console.error("Voice processing error:", err);
      setErrorMsg(
        detectedLang === "hi"
          ? "उत्तर तैयार करने में समस्या आई। पुनः प्रयास करें।"
          : detectedLang === "en"
          ? "Could not process voice input. Please try again."
          : "उत्तर तयार करताना अडचण आली. कृपया पुन्हा प्रयत्न करा."
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const { status, startListening, stopListening } = useSpeechRecognition({
    language: activeLang,
    onTranscript: handleSpeechCaptured,
  });

  // Start listening and unlock audio on initial view mount
  useEffect(() => {
    unlockAudio();
    startListening();
    return () => {
      stopListening();
      stopSpeaking();
    };
  }, []);

  const handleMicClick = () => {
    unlockAudio();
    if (status === "listening") {
      stopListening();
    } else {
      setUserTranscript("");
      setAiResponse(null);
      setErrorMsg(null);
      stopSpeaking();
      startListening();
    }
  };

  const handleStopClick = () => {
    stopSpeaking();
  };

  const handleSpeakAgainClick = () => {
    unlockAudio();
    stopSpeaking();
    setUserTranscript("");
    setAiResponse(null);
    setErrorMsg(null);
    startListening();
  };

  const handleSampleClick = () => {
    const text =
      activeLang === "hi"
        ? "मेरी फसल का नुकसान हो गया है, मुझे क्या करना चाहिए?"
        : activeLang === "en"
        ? "My crop suffered damage, what steps should I take?"
        : "माझ्या पिकाचे नुकसान झाले आहे, मला काय करावे?";
    handleSpeechCaptured(text);
  };

  const samplePrompt =
    activeLang === "hi"
      ? "उदा. — मेरी फसल का नुकसान हो गया है, मुझे क्या करना चाहिए?"
      : activeLang === "en"
      ? "e.g. — My crop suffered damage, what steps should I take?"
      : "उदा. — माझ्या पिकाचे नुकसान झाले आहे, मला काय करावे?";

  const titleText =
    activeLang === "hi"
      ? "हिंदी (बोलकर पूछें)"
      : activeLang === "en"
      ? "English (Voice Active)"
      : "मराठी (बोलून विचारा)";

  // Status Labels
  let statusLabel =
    activeLang === "hi" ? "सुन रहा हूँ..." : activeLang === "en" ? "Listening..." : "ऐकत आहे...";

  if (isProcessing) {
    statusLabel =
      activeLang === "hi"
        ? "समझ रहा हूँ..."
        : activeLang === "en"
        ? "Understanding query..."
        : "समजून घेत आहे...";
  } else if (isSpeaking) {
    statusLabel =
      activeLang === "hi"
        ? "उत्तर बता रहा हूँ..."
        : activeLang === "en"
        ? "SahkaarSetu Speaking..."
        : "उत्तर सांगत आहे...";
  } else if (aiResponse) {
    statusLabel =
      activeLang === "hi"
        ? "पुनः पूछ सकते हैं"
        : activeLang === "en"
        ? "Ready for next question"
        : "पुन्हा विचारू शकता";
  }

  // Dynamic Intent Label based on detected intent
  const currentIntent = aiResponse?.intent || "CASUAL_GREETING";
  const intentLabel =
    INTENT_LABELS[currentIntent]?.[activeLang] ||
    INTENT_LABELS[currentIntent]?.mr ||
    INTENT_LABELS["GENERAL_COOPERATIVE"][activeLang] ||
    "SAHKAARSETU";

  const langDisplayName = LANG_DISPLAY_NAMES[activeLang] || activeLang;

  return (
    <div className="voice-mode-overlay" role="dialog" aria-label="Voice Assistance">
      {/* Header */}
      <div className="voice-mode-header">
        <div className="voice-mode-brand">
          <SahkaarSetuLogo size={24} color="#FFFFFF" />
          <span className="voice-mode-name">SahkaarSetu Voice</span>
        </div>
        <div className="voice-mode-lang">{titleText}</div>
        <button
          type="button"
          className="voice-mode-close"
          onClick={onClose}
          aria-label="Close voice mode"
        >
          ×
        </button>
      </div>

      {/* Main Central Voice Stage */}
      <div className="voice-mode-stage">
        {/* Animated Microphone Orb */}
        <div className="voice-orb-container">
          <div
            className={`voice-orb ${
              status === "listening"
                ? "voice-orb--listening"
                : isProcessing
                ? "voice-orb--processing"
                : isSpeaking
                ? "voice-orb--speaking"
                : ""
            }`}
            onClick={handleMicClick}
            aria-label="Toggle Microphone"
          >
            <MicIcon size={36} color="#FFFFFF" />
          </div>
          {status === "listening" && <div className="voice-pulse-ring" />}
        </div>

        {/* Dynamic Status Label */}
        <div className="voice-status-text">{statusLabel}</div>

        {/* User Recognized Transcript Card */}
        {userTranscript && (
          <div className="voice-user-transcript">
            <div className="transcript-meta-row">
              <span className="transcript-label">
                {activeLang === "hi" ? "आपने कहा:" : activeLang === "en" ? "YOU SAID:" : "तुम्ही म्हणालात:"}
              </span>
              <div className="transcript-tags">
                <span className="transcript-tag-lang">🌐 {langDisplayName}</span>
                {aiResponse && <span className="transcript-tag-intent">📌 {intentLabel}</span>}
              </div>
            </div>
            <p className="transcript-body">"{userTranscript}"</p>
          </div>
        )}

        {/* Sample Prompt Chip (Shown before user speaks) */}
        {!userTranscript && !isProcessing && (
          <button
            type="button"
            className="voice-sample-chip"
            onClick={handleSampleClick}
          >
            <span>{samplePrompt}</span>
          </button>
        )}

        {/* Error Bar */}
        {errorMsg && <div className="voice-error-bar">{errorMsg}</div>}

        {/* Spoken AI Response Card */}
        {aiResponse && (
          <div className="voice-response-card">
            <div className="voice-response-header">
              <ShieldCheckIcon size={16} color="#126B62" />
              <span>{intentLabel}</span>
            </div>

            <p className="voice-response-summary">{aiResponse.content}</p>

            {/* Playback & Voice Action Controls */}
            <div className="voice-controls-row">
              {isSpeaking ? (
                <button
                  type="button"
                  className="voice-control-btn voice-control-btn--active"
                  onClick={handleStopClick}
                >
                  <PauseIcon size={16} />
                  <span>{activeLang === "hi" ? "रोकें" : activeLang === "en" ? "Stop" : "थांबवा"}</span>
                </button>
              ) : (
                <button
                  type="button"
                  className="voice-control-btn"
                  onClick={() =>
                    aiResponse && speak(aiResponse.id, aiResponse.content, aiResponse.language || activeLang)
                  }
                >
                  <SpeakerIcon size={16} />
                  <span>
                    {activeLang === "hi" ? "ऐकें" : activeLang === "en" ? "Listen" : "ऐका"}
                  </span>
                </button>
              )}

              {/* Continuous Voice Conversation: Speak Again */}
              <button
                type="button"
                className="voice-control-btn voice-control-btn--primary"
                onClick={handleSpeakAgainClick}
              >
                <MicIcon size={16} color="#FFFFFF" />
                <span>
                  {activeLang === "hi" ? "फिर बोलें" : activeLang === "en" ? "Speak Again" : "पुन्हा बोला"}
                </span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer Shortcut to Full Chat View */}
      {onNavigateToChat && (
        <div className="voice-mode-footer">
          <button
            type="button"
            className="voice-chat-shortcut"
            onClick={() => {
              onClose();
              onNavigateToChat();
            }}
          >
            <span>
              {activeLang === "hi"
                ? "लिखित चैट उत्तर देखें"
                : activeLang === "en"
                ? "View Detailed Text Chat"
                : "सविस्तर मजकूर चॅट पाहा"}
            </span>
            <ArrowRightIcon size={14} />
          </button>
        </div>
      )}
    </div>
  );
};

export default VoiceModeView;
