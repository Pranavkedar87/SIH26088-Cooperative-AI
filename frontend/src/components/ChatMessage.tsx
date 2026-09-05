import React, { useCallback } from "react";
import type { ChatMessage as ChatMessageType, LanguageCode } from "../types";
import { parseAnswer } from "../utils/parseAnswer";
import StructuredAnswer from "./StructuredAnswer";
import SourcesAccordion from "./SourcesAccordion";

interface Props {
  message: ChatMessageType;
  onSpeak?: (id: string, text: string, language: LanguageCode) => void;
  isSpeaking?: boolean;
  onFollowUp?: (prompt: string) => void;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

const ChatMessage: React.FC<Props> = ({
  message,
  onSpeak,
  isSpeaking = false,
  onFollowUp,
}) => {
  const isUser = message.role === "user";
  const hasSources = !isUser && message.sources && message.sources.length > 0;

  // Parse structured sections for assistant messages
  const sections = !isUser ? parseAnswer(message.content) : null;

  const handleSpeakClick = useCallback(() => {
    if (onSpeak) onSpeak(message.id, message.content, message.language);
  }, [onSpeak, message.id, message.content, message.language]);

  const handleCopy = useCallback(() => {
    navigator.clipboard?.writeText(message.content).catch(() => {});
  }, [message.content]);

  const handleFollowUp = useCallback(() => {
    if (onFollowUp) onFollowUp("Can you explain more about the above?");
  }, [onFollowUp]);

  return (
    <div className={`chat-message chat-message--${message.role}`}>
      <div className="chat-message__avatar" aria-hidden="true">
        {isUser ? "👤" : "🤝"}
      </div>

      <div className="chat-message__bubble">
        {/* Message content */}
        {isUser || !sections ? (
          <p className="chat-message__text">{message.content}</p>
        ) : (
          <StructuredAnswer sections={sections} />
        )}

        {/* Grounded badge — only for assistant with sources */}
        {hasSources && (
          <div className="grounded-badge" aria-label="Grounded answer">
            🔎 Grounded Answer
          </div>
        )}

        {/* Collapsible sources */}
        {hasSources && (
          <SourcesAccordion sources={message.sources!} />
        )}

        {/* Answer actions — only for assistant */}
        {!isUser && (
          <div className="answer-actions">
            {onSpeak && (
              <button
                type="button"
                className={`action-btn ${isSpeaking ? "action-btn--speaking" : ""}`}
                onClick={handleSpeakClick}
                aria-label={isSpeaking ? "Stop reading" : "Read answer aloud"}
                title={isSpeaking ? "Stop reading" : "Read aloud"}
              >
                {isSpeaking ? "⏹ Stop" : "🔊 Read"}
              </button>
            )}
            {navigator.clipboard && (
              <button
                type="button"
                className="action-btn"
                onClick={handleCopy}
                aria-label="Copy answer"
                title="Copy to clipboard"
              >
                📋 Copy
              </button>
            )}
            {onFollowUp && (
              <button
                type="button"
                className="action-btn"
                onClick={handleFollowUp}
                aria-label="Ask a follow-up question"
                title="Ask a follow-up"
              >
                ↩ Follow up
              </button>
            )}
          </div>
        )}

        {/* Timestamp */}
        <div className="chat-message__footer">
          <span className="chat-message__time">{formatTime(message.timestamp)}</span>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
