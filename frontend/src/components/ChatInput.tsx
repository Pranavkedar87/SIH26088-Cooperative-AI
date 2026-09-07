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

const PLACEHOLDER: Record<string, string> = {
  en: "Ask me anything — schemes, science, history, or any topic…",
  hi: "कुछ भी पूछें — योजनाएं, विज्ञान, इतिहास, या कोई भी विषय…",
  mr: "काहीही विचारा — योजना, विज्ञान, इतिहास किंवा कोणताही विषय…",
};

const STT_STATUS_LABEL: Record<string, { listening: string; processing: string }> = {
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
        textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
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
      el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
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
    <div className="input-bar-container">
      {/* Listening or processing status badge */}
      {status === "listening" && (
        <div className="stt-status-bar stt-status-bar--listening" role="status" aria-live="polite">
          <MicIcon size={14} color="#B94A48" />
          <span>{(STT_STATUS_LABEL[language] ?? STT_STATUS_LABEL.en).listening}</span>
        </div>
      )}
      {status === "processing" && (
        <div className="stt-status-bar stt-status-bar--processing" role="status" aria-live="polite">
          <span>{(STT_STATUS_LABEL[language] ?? STT_STATUS_LABEL.en).processing}</span>
        </div>
      )}
      {errorMessage && status === "error" && (
        <div className="stt-status-bar stt-status-bar--error" role="alert">
          <span>{errorMessage}</span>
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

      <div className="input-sticky-bar">
        <textarea
          ref={textareaRef}
          className="input-textarea"
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={PLACEHOLDER[language] ?? PLACEHOLDER.en}
          rows={1}
          disabled={isLoading}
          aria-label="Message input"
          maxLength={2000}
        />

        {/* Microphone Button */}
        <button
          type="button"
          className={`input-btn mic-btn ${status === "listening" ? "mic-btn--active" : ""}`}
          onClick={handleMicClick}
          disabled={isLoading}
          aria-label={status === "listening" ? "Stop voice input" : "Start voice input"}
          title={
            !isSupported
              ? "Voice input not supported"
              : status === "listening"
              ? "Listening… Click to stop"
              : "Click to speak"
          }
        >
          <MicIcon size={18} color={status === "listening" ? "#B94A48" : "#126B62"} />
        </button>

        {/* Send Button */}
        <button
          type="button"
          className="input-btn send-btn"
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
