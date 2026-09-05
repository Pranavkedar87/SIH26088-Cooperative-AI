import React, { useEffect, useState } from "react";
import type { LanguageCode, ChatMessage } from "../types";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";
import { useTextToSpeech } from "../hooks/useTextToSpeech";
import { sendQuery } from "../api/client";
import { parseGuidance } from "../utils/guidanceParser";
import { SahkaarSetuLogo, MicIcon, PauseIcon, SpeakerIcon, ArrowRightIcon, ShieldCheckIcon } from "./Icons";

interface Props {
  language: LanguageCode;
  onClose: () => void;
  onNavigateToChat?: () => void;
}

export const VoiceModeView: React.FC<Props> = ({
  language,
  onClose,
  onNavigateToChat,
}) => {
  const [userTranscript, setUserTranscript] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [aiResponse, setAiResponse] = useState<ChatMessage | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { speak, isSpeaking, stop: stopSpeaking } = useTextToSpeech();

  const samplePrompt =
    language === "hi"
      ? "उदा. — मेरी फसल का नुकसान हो गया है, मुझे क्या करना चाहिए?"
      : language === "en"
      ? "e.g. — My crop suffered damage, what steps should I take?"
      : "उदा. — माझ्या पिकाचे नुकसान झाले आहे, मला काय करावे?";

  const titleText =
    language === "hi"
      ? "हिंदी में बोलें"
      : language === "en"
      ? "Speak in English"
      : "मराठीत बोला";

  const handleSpeechCaptured = async (text: string) => {
    if (!text || !text.trim() || isProcessing) return;
    const trimmed = text.trim();
    setUserTranscript(trimmed);
    setIsProcessing(true);
    setErrorMsg(null);
    stopSpeaking();

    try {
      const response = await sendQuery({
        message: trimmed,
        language,
      });

      const assistantMsg: ChatMessage = {
        id: `voice-msg-${Date.now()}`,
        role: "assistant",
        content: response.answer,
        timestamp: new Date(),
        language: response.language,
        sources: response.sources,
        intent: response.intent,
      };

      setAiResponse(assistantMsg);

      // AUTOMATIC VOICE-FIRST PLAYBACK
      // Parse summary/guidance and speak aloud automatically
      const parsed = parseGuidance(response.answer, response.language);
      const spokenText = parsed.summary || response.answer.slice(0, 200);
      speak(assistantMsg.id, spokenText, response.language);
    } catch (err) {
      console.error("Voice mode error:", err);
      setErrorMsg(
        language === "hi"
          ? "आवाज संसाधित करने में समस्या आई। पुनः प्रयास करें।"
          : language === "en"
          ? "Could not process voice input. Please try again."
          : "आवाज प्रक्रिया करताना अडचण आली. कृपया पुन्हा प्रयत्न करा."
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const { status, startListening, stopListening } = useSpeechRecognition({
    language,
    onTranscript: handleSpeechCaptured,
  });

  // Start listening on initial view open
  useEffect(() => {
    startListening();
    return () => {
      stopListening();
      stopSpeaking();
    };
  }, []);

  const handleMicClick = () => {
    if (status === "listening") {
      stopListening();
    } else {
      setUserTranscript("");
      setAiResponse(null);
      stopSpeaking();
      startListening();
    }
  };

  const handleSampleClick = () => {
    const text =
      language === "hi"
        ? "मेरी फसल का नुकसान हो गया है, PMFBY में क्या करें?"
        : language === "en"
        ? "My crop suffered damage, what steps under PMFBY?"
        : "माझ्या पिकाचे नुकसान झाले आहे, PMFBY मध्ये काय करावे?";
    handleSpeechCaptured(text);
  };

  // Status Labels
  let statusLabel = language === "hi" ? "सुन रहा हूँ..." : language === "en" ? "Listening..." : "ऐकत आहे...";
  if (isProcessing) {
    statusLabel =
      language === "hi"
        ? "उत्तर तैयार हो रहा है..."
        : language === "en"
        ? "Preparing guidance..."
        : "उत्तर तयार होत आहे...";
  } else if (isSpeaking) {
    statusLabel =
      language === "hi"
        ? "उत्तर दे रहा हूँ..."
        : language === "en"
        ? "SahkaarSetu Speaking..."
        : "उत्तर देत आहे...";
  } else if (aiResponse) {
    statusLabel =
      language === "hi"
        ? "मार्गदर्शन प्राप्त हुआ"
        : language === "en"
        ? "Guidance Ready"
        : "मार्गदर्शन मिळाले";
  }

  const parsedGuidance = aiResponse ? parseGuidance(aiResponse.content, language) : null;

  return (
    <div className="voice-mode-overlay" role="dialog" aria-label="Voice Assistance">
      {/* Header */}
      <div className="voice-mode-header">
        <div className="voice-mode-brand">
          <SahkaarSetuLogo size={24} color="#126B62" />
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
          >
            <MicIcon size={36} color="#FFFFFF" />
          </div>
          {status === "listening" && <div className="voice-pulse-ring" />}
        </div>

        {/* Dynamic Status Label */}
        <div className="voice-status-text">{statusLabel}</div>

        {/* User Recognized Transcript */}
        {userTranscript && (
          <div className="voice-user-transcript">
            <span className="transcript-label">
              {language === "hi" ? "आपने कहा:" : language === "en" ? "You said:" : "तुम्ही म्हणालात:"}
            </span>
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
        {parsedGuidance && (
          <div className="voice-response-card">
            <div className="voice-response-header">
              <ShieldCheckIcon size={16} color="#126B62" />
              <span>{parsedGuidance.domainLabel}</span>
            </div>

            <p className="voice-response-summary">{parsedGuidance.summary}</p>

            {/* Playback Controls */}
            <div className="voice-controls-row">
              {isSpeaking ? (
                <button
                  type="button"
                  className="voice-control-btn voice-control-btn--active"
                  onClick={stopSpeaking}
                >
                  <PauseIcon size={16} />
                  <span>{language === "hi" ? "रोकें" : language === "en" ? "Stop" : "थांबवा"}</span>
                </button>
              ) : (
                <button
                  type="button"
                  className="voice-control-btn"
                  onClick={() =>
                    aiResponse && speak(aiResponse.id, parsedGuidance.summary, language)
                  }
                >
                  <SpeakerIcon size={16} />
                  <span>
                    {language === "hi" ? "फिर से सुनें" : language === "en" ? "Listen Again" : "पुन्हा ऐका"}
                  </span>
                </button>
              )}

              {/* Repeat Speak CTA */}
              <button
                type="button"
                className="voice-control-btn voice-control-btn--primary"
                onClick={handleMicClick}
              >
                <MicIcon size={16} color="#FFFFFF" />
                <span>
                  {language === "hi" ? "फिर बोलें" : language === "en" ? "Speak Again" : "पुन्हा बोला"}
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
              {language === "hi"
                ? "लिखित चैट उत्तर देखें"
                : language === "en"
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
