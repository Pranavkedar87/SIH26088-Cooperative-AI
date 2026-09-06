import React, { useEffect, useState, useRef, useCallback } from "react";
import type { LanguageCode, ChatMessage, VoiceState } from "../types";
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
  ta: "தமிழ்",
  te: "తెలుగు",
  kn: "ಕನ್ನಡ",
  gu: "ગુજરાતી",
  bn: "বাংলা",
  pa: "ਪੰਜਾਬੀ",
  ml: "മലയാളം",
};

// Strips raw markdown for visual card display in Voice Mode
function stripMarkdown(text: string): string {
  if (!text) return "";
  return text
    .replace(/https?:\/\/\S+/g, "")
    .replace(/#+\s*/g, "")
    .replace(/[\*\_\`]/g, "")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .trim();
}

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
  const [voiceState, setVoiceState] = useState<VoiceState>("IDLE");
  const [userTranscript, setUserTranscript] = useState<string>("");
  const [aiResponse, setAiResponse] = useState<ChatMessage | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const voiceStateRef = useRef<VoiceState>(voiceState);
  useEffect(() => {
    voiceStateRef.current = voiceState;
  }, [voiceState]);

  // Forward declaration of TTS completion callback
  const handleTTSEnd = useCallback(() => {
    console.info("[VOICE_STATE] TTS finished naturally -> transitioning to FOLLOW_UP_LISTENING");
    setVoiceState("FOLLOW_UP_LISTENING");
  }, []);

  const { speak, stop: stopSpeaking, unlockAudio } = useTextToSpeech({
    onEnd: handleTTSEnd,
  });

  const handleSpeechCaptured = async (text: string) => {
    if (!text || !text.trim() || voiceStateRef.current === "PROCESSING" || voiceStateRef.current === "THINKING") {
      return;
    }

    const startTime = performance.now();
    const trimmed = text.trim();

    stopSpeaking();
    unlockAudio();

    setUserTranscript(trimmed);
    setVoiceState("PROCESSING");
    setErrorMsg(null);

    // 1. Detect language from spoken input
    const detectedLang = detectLanguageFromText(trimmed, activeLang);
    setActiveLang(detectedLang);

    // 2. Transition to THINKING while querying backend
    setVoiceState("THINKING");

    try {
      // Query backend with response_mode = "voice" for fast concise spoken answer
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

      const cleanedAnswer = stripMarkdown(response.answer);

      const assistantMsg: ChatMessage = {
        id: `voice-msg-${Date.now()}`,
        role: "assistant",
        content: cleanedAnswer,
        timestamp: new Date(),
        language: response.language || detectedLang,
        sources: response.sources,
        intent: response.intent,
      };

      setAiResponse(assistantMsg);

      // 3. Transition to SPEAKING state and trigger automatic TTS audio
      setVoiceState("SPEAKING");
      const targetLang = response.language || detectedLang;

      speak(assistantMsg.id, cleanedAnswer, targetLang, () => {
        console.info("[VOICE_STATE] Spoken response completed -> transitioning to FOLLOW_UP_LISTENING");
        setVoiceState("FOLLOW_UP_LISTENING");
      });
    } catch (err) {
      console.error("[VOICE_ERROR] Voice processing error:", err);
      setVoiceState("ERROR");
      setErrorMsg(
        detectedLang === "hi"
          ? "उत्तर तैयार करने में समस्या आई। पुनः प्रयास करें।"
          : detectedLang === "en"
          ? "Could not process voice input. Please try again."
          : "उत्तर तयार करताना अडचण आली. कृपया पुन्हा प्रयत्न करा."
      );
    }
  };

  const { status: sttStatus, errorMessage: sttError, startListening, stopListening } = useSpeechRecognition({
    language: activeLang,
    onTranscript: handleSpeechCaptured,
    sessionId: sessionId,
  });

  // Sync STT hook status & error messages into VoiceModeView state
  useEffect(() => {
    if (sttStatus === "processing") {
      setVoiceState("PROCESSING");
    } else if (sttStatus === "error" && sttError) {
      setVoiceState("ERROR");
      setErrorMsg(sttError);
    }
  }, [sttStatus, sttError]);

  // Automatically start listening when entering FOLLOW_UP_LISTENING or LISTENING state
  useEffect(() => {
    if (voiceState === "LISTENING" || voiceState === "FOLLOW_UP_LISTENING") {
      unlockAudio();
      startListening();
    }
  }, [voiceState, activeLang, unlockAudio, startListening]);

  // Initial setup on view mount
  useEffect(() => {
    unlockAudio();
    setVoiceState("LISTENING");
    return () => {
      stopListening();
      stopSpeaking();
    };
  }, []);

  // Mic Orb click handler (Supports Interruption!)
  const handleOrbClick = () => {
    unlockAudio();

    if (voiceState === "SPEAKING") {
      // INTERRUPT SPEAKING immediately and start listening for follow-up!
      console.info("[VOICE_INTERRUPT] User interrupted AI speech -> starting STT listening");
      stopSpeaking();
      setUserTranscript("");
      setAiResponse(null);
      setErrorMsg(null);
      setVoiceState("FOLLOW_UP_LISTENING");
    } else if (voiceState === "LISTENING" || voiceState === "FOLLOW_UP_LISTENING") {
      stopListening();
      setVoiceState("IDLE");
    } else {
      // IDLE or ERROR -> start listening
      setUserTranscript("");
      setAiResponse(null);
      setErrorMsg(null);
      stopSpeaking();
      setVoiceState("LISTENING");
    }
  };

  const handleStopSpeakingClick = () => {
    stopSpeaking();
    setVoiceState("FOLLOW_UP_LISTENING");
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

  // Dynamic Status Badge Labels according to Voice State Machine
  const stateBadgeMap: Record<VoiceState, Record<string, { label: string; tag: string }>> = {
    IDLE: {
      mr: { label: "तयार", tag: "मायक्रोफोनवर टॅप करा" },
      hi: { label: "तैयार", tag: "माइक पर टैप करें" },
      en: { label: "Ready", tag: "Tap mic to speak" },
    },
    LISTENING: {
      mr: { label: "ऐकत आहे", tag: "तुमचा प्रश्न विचारा..." },
      hi: { label: "सुन रहा हूँ", tag: "अपना प्रश्न पूछें..." },
      en: { label: "Listening", tag: "Ask your question..." },
    },
    PROCESSING: {
      mr: { label: "प्रोसेस करत आहे", tag: "भाषा आणि प्रश्न समजून घेत आहे..." },
      hi: { label: "प्रोसेस कर रहा हूँ", tag: "भाषा और प्रश्न समझ रहा हूँ..." },
      en: { label: "Processing", tag: "Understanding spoken input..." },
    },
    THINKING: {
      mr: { label: "माहिती शोधत आहे", tag: "सहकारी दस्तऐवज तपासत आहे..." },
      hi: { label: "जानकारी खोज रहा हूँ", tag: "सहकारी दस्तावेज जाँच रहा हूँ..." },
      en: { label: "Thinking", tag: "Searching cooperative documents..." },
    },
    SPEAKING: {
      mr: { label: "उत्तर सांगत आहे", tag: "थांबवण्यासाठी किंवा प्रश्न विचारण्यासाठी टॅप करा" },
      hi: { label: "उत्तर बता रहा हूँ", tag: "रोकने या बोलने के लिए टैप करें" },
      en: { label: "Speaking", tag: "Tap to interrupt & speak" },
    },
    FOLLOW_UP_LISTENING: {
      mr: { label: "पुढचा प्रश्न विचारा", tag: "Continuous Assistant Active 🎙️" },
      hi: { label: "अगला प्रश्न पूछें", tag: "Continuous Assistant Active 🎙️" },
      en: { label: "Listening for follow-up", tag: "Continuous Assistant Active 🎙️" },
    },
    ERROR: {
      mr: { label: "त्रुटी", tag: "पुन्हा प्रयत्न करण्यासाठी मायक्रोफोनवर टॅप करा" },
      hi: { label: "त्रुटि", tag: "पुनः प्रयास करने के लिए माइक पर टैप करें" },
      en: { label: "Error", tag: "Tap mic to try again" },
    },
  };

  const currentBadge = stateBadgeMap[voiceState]?.[activeLang] || stateBadgeMap[voiceState]?.mr;

  // Dynamic Intent Label based on detected intent
  const currentIntent = aiResponse?.intent || "CASUAL_GREETING";
  const intentLabel =
    INTENT_LABELS[currentIntent]?.[activeLang] ||
    INTENT_LABELS[currentIntent]?.mr ||
    INTENT_LABELS["GENERAL_COOPERATIVE"][activeLang] ||
    "SAHKAARSETU";

  const langDisplayName = LANG_DISPLAY_NAMES[activeLang] || activeLang;

  return (
    <div className="voice-mode-overlay" role="dialog" aria-label="SahkaarSetu Voice Assistant">
      {/* Header */}
      <div className="voice-mode-header">
        <div className="voice-mode-brand">
          <SahkaarSetuLogo size={24} color="#FFFFFF" />
          <span className="voice-mode-name">SahkaarSetu Voice</span>
        </div>

        {/* State Machine Status Badge */}
        <div className="voice-state-pill">
          <span className={`voice-state-dot voice-state-dot--${voiceState.toLowerCase()}`} />
          <span className="voice-state-text">
            {langDisplayName} • {currentBadge.label}
          </span>
        </div>

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
            className={`voice-orb voice-orb--${voiceState.toLowerCase()}`}
            onClick={handleOrbClick}
            aria-label="Toggle Microphone"
          >
            {voiceState === "SPEAKING" ? (
              <SpeakerIcon size={36} color="#FFFFFF" />
            ) : (
              <MicIcon size={36} color="#FFFFFF" />
            )}
          </div>
          {(voiceState === "LISTENING" || voiceState === "FOLLOW_UP_LISTENING") && (
            <div className="voice-pulse-ring" />
          )}
          {voiceState === "SPEAKING" && <div className="voice-wave-ring" />}
        </div>

        {/* Dynamic Status Subtitle */}
        <div className="voice-status-text">{currentBadge.tag}</div>

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
        {!userTranscript && (voiceState === "IDLE" || voiceState === "LISTENING") && (
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
              {voiceState === "SPEAKING" ? (
                <button
                  type="button"
                  className="voice-control-btn voice-control-btn--active"
                  onClick={handleStopSpeakingClick}
                >
                  <PauseIcon size={16} />
                  <span>{activeLang === "hi" ? "रोकें (बोलें)" : activeLang === "en" ? "Stop & Speak" : "थांबवा (बोलण्यासाठी)"}</span>
                </button>
              ) : (
                <button
                  type="button"
                  className="voice-control-btn"
                  onClick={() => {
                    setVoiceState("SPEAKING");
                    speak(aiResponse.id, aiResponse.content, aiResponse.language || activeLang, () => {
                      setVoiceState("FOLLOW_UP_LISTENING");
                    });
                  }}
                >
                  <SpeakerIcon size={16} />
                  <span>
                    {activeLang === "hi" ? "फिर ऐकें" : activeLang === "en" ? "Listen Again" : "पुन्हा ऐका"}
                  </span>
                </button>
              )}

              {/* Continuous Voice Assistant Indicator */}
              <div className="voice-continuous-indicator">
                <span className="voice-continuous-dot" />
                <span>Continuous Voice Active</span>
              </div>
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
