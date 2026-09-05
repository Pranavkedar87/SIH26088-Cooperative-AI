import React, { useRef, useCallback } from "react";
import type { LanguageCode } from "../types";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";

interface Props {
  language: LanguageCode;
  isLoading: boolean;
  onSend: (message: string) => void;
  value: string;
  onChange: (value: string) => void;
}

const PLACEHOLDER: Record<LanguageCode, string> = {
  en: "Ask your question about cooperatives, schemes, or laws…",
  hi: "सहकारी समितियों, योजनाओं या कानूनों के बारे में अपना प्रश्न पूछें…",
  mr: "सहकारी संस्था, योजना किंवा कायद्याबद्दल प्रश्न विचारा…",
};

const STT_STATUS_LABEL: Record<LanguageCode, { listening: string; processing: string }> = {
  en: { listening: "Listening… Speak now", processing: "Processing speech…" },
  hi: { listening: "सुन रहा हूँ… अब बोलें", processing: "आवाज संसाधित हो रही है…" },
  mr: { listening: "ऐकत आहे… आता बोला", processing: "आवाज प्रक्रिया सुरू आहे…" },
};

const ChatInput: React.FC<Props> = ({ language, isLoading, onSend, value, onChange }) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleTranscript = useCallback(
    (text: string) => {
      const newText = value ? `${value} ${text}` : text;
      onChange(newText);
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
        textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
        textareaRef.current.focus();
      }
    },
    [value, onChange]
  );


  const { status, errorMessage, startListening, stopListening, clearError, isSupported } =
    useSpeechRecognition({
      language,
      onTranscript: handleTranscript,
    });

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    if (status === "listening") {
      stopListening();
    }
    clearError();
    onSend(trimmed);
    onChange("");
    textareaRef.current?.focus();
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (errorMessage) {
      clearError();
    }
    onChange(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  };

  const handleMicClick = () => {
    if (status === "listening") {
      stopListening();
    } else {
      clearError();
      startListening();
    }
  };

  return (
    <div className="chat-input-wrapper">
      {/* Listening or processing status badge */}
      {status === "listening" && (
        <div className="stt-status-badge stt-status-badge--listening" role="status" aria-live="polite">
          <span className="pulse-dot" /> {STT_STATUS_LABEL[language].listening}
        </div>
      )}
      {status === "processing" && (
        <div className="stt-status-badge stt-status-badge--processing" role="status" aria-live="polite">
          ⏳ {STT_STATUS_LABEL[language].processing}
        </div>
      )}
      {errorMessage && status === "error" && (
        <div className="stt-status-badge stt-status-badge--error" role="alert">
          <span>⚠️ {errorMessage}</span>
          <button
            type="button"
            className="stt-error-dismiss"
            onClick={clearError}
            aria-label="Dismiss message"
          >
            ×
          </button>
        </div>
      )}

      <div className="chat-input-bar">
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={PLACEHOLDER[language]}
          rows={1}
          disabled={isLoading}
          aria-label="Message input"
          maxLength={2000}
        />

        {/* Interactive Microphone Button */}
        <button
          type="button"
          className={`icon-btn mic-btn ${status === "listening" ? "mic-btn--active" : ""}`}
          onClick={handleMicClick}
          disabled={isLoading}
          aria-label={
            status === "listening" ? "Stop voice input" : "Start voice input"
          }
          title={
            !isSupported
              ? "Voice input is not supported in this browser"
              : status === "listening"
              ? "Listening... Click to stop"
              : "Click to speak"
          }
        >
          {status === "listening" ? "🔴" : status === "processing" ? "⏳" : "🎤"}
        </button>

        <button
          type="button"
          className="send-btn"
          onClick={handleSend}
          disabled={!value.trim() || isLoading}
          aria-label="Send message"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatInput;
