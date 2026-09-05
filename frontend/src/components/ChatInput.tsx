import React, { useRef, useCallback } from "react";
import type { LanguageCode } from "../types";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";
import { MicIcon, SendIcon } from "./Icons";

interface Props {
  language: LanguageCode;
  isLoading: boolean;
  onSend: (message: string) => void;
  value: string;
  onChange: (value: string) => void;
}

const PLACEHOLDER: Record<LanguageCode, string> = {
  en: "Ask your question about cooperative services, schemes, or laws…",
  hi: "सहकारी सेवाओं, योजनाओं या नियमों के बारे में अपना प्रश्न पूछें…",
  mr: "सहकारी सेवा, योजना किंवा कायद्याबद्दल प्रश्न विचारा…",
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
        textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
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
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.focus();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (errorMessage) {
      clearError();
    }
    onChange(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
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
    <div className="input-container">
      {/* Listening or processing status badge */}
      {status === "listening" && (
        <div className="stt-badge stt-badge--listening" role="status" aria-live="polite">
          <span className="stt-red-dot">🔴</span>
          <span>{STT_STATUS_LABEL[language].listening}</span>
        </div>
      )}
      {status === "processing" && (
        <div className="stt-badge stt-badge--processing" role="status" aria-live="polite">
          <span>⏳ {STT_STATUS_LABEL[language].processing}</span>
        </div>
      )}
      {errorMessage && status === "error" && (
        <div className="stt-badge stt-badge--error" role="alert">
          <span>⚠️ {errorMessage}</span>
          <button
            type="button"
            className="stt-dismiss-btn"
            onClick={clearError}
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}

      <div className="input-bar">
        <textarea
          ref={textareaRef}
          className="input-bar__textarea"
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={PLACEHOLDER[language]}
          rows={1}
          disabled={isLoading}
          aria-label="Ask a question"
          maxLength={2000}
        />

        {/* Microphone Button */}
        <button
          type="button"
          className={`input-bar__btn mic-btn ${status === "listening" ? "mic-btn--listening" : ""}`}
          onClick={handleMicClick}
          disabled={isLoading}
          aria-label={status === "listening" ? "Stop listening" : "Start voice input"}
          title={
            !isSupported
              ? "Voice input not supported"
              : status === "listening"
              ? "Listening… Click to stop"
              : "Click to speak"
          }
        >
          <MicIcon size={18} color={status === "listening" ? "#E57373" : "#145A62"} />
        </button>

        {/* Send Button */}
        <button
          type="button"
          className="input-bar__btn send-btn"
          onClick={handleSend}
          disabled={!value.trim() || isLoading}
          aria-label="Send message"
        >
          <SendIcon size={18} color="#FFFFFF" />
        </button>
      </div>
    </div>
  );
};

export default ChatInput;
