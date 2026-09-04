import React, { useRef } from "react";
import type { LanguageCode } from "../types";

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

const ChatInput: React.FC<Props> = ({ language, isLoading, onSend, value, onChange }) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    onChange("");
    textareaRef.current?.focus();
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    // Auto-grow textarea
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  };

  return (
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

      {/* Mic button — placeholder for Milestone 3 (web voice) */}
      <button
        className="icon-btn mic-btn"
        aria-label="Voice input (coming soon)"
        disabled
        title="Voice input — coming in next milestone"
      >
        🎤
      </button>

      <button
        className="send-btn"
        onClick={handleSend}
        disabled={!value.trim() || isLoading}
        aria-label="Send message"
      >
        Send
      </button>
    </div>
  );
};

export default ChatInput;
