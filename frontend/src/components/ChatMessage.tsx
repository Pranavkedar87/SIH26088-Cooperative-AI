import React, { useCallback } from "react";
import type { ChatMessage as ChatMessageType, LanguageCode } from "../types";
import { parseAnswer } from "../utils/parseAnswer";
import StructuredAnswer from "./StructuredAnswer";
import SourcesAccordion from "./SourcesAccordion";
import { SpeakerIcon, CopyIcon, CheckVerifiedIcon } from "./Icons";

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
    if (onFollowUp) onFollowUp("Can you provide more details about this service?");
  }, [onFollowUp]);

  return (
    <div className={`chat-row chat-row--${message.role}`}>
      <div className="chat-card">
        {/* User prompt or Assistant response */}
        {isUser || !sections ? (
          <p className="chat-card__text">{message.content}</p>
        ) : (
          <StructuredAnswer sections={sections} />
        )}

        {/* Grounded verification tag */}
        {hasSources && (
          <div className="grounded-tag" aria-label="Grounded answer">
            <CheckVerifiedIcon size={12} color="#2A7B4C" />
            <span>Grounded Answer</span>
          </div>
        )}

        {/* Sources Accordion */}
        {hasSources && <SourcesAccordion sources={message.sources!} />}

        {/* Action Controls for Assistant */}
        {!isUser && (
          <div className="chat-card__actions">
            {onSpeak && (
              <button
                type="button"
                className={`action-pill ${isSpeaking ? "action-pill--active" : ""}`}
                onClick={handleSpeakClick}
                aria-label={isSpeaking ? "Stop reading" : "Read aloud"}
                title={isSpeaking ? "Stop reading" : "Read aloud"}
              >
                <SpeakerIcon size={14} />
                <span>{isSpeaking ? "Stop" : "Read Aloud"}</span>
              </button>
            )}
            {navigator.clipboard && (
              <button
                type="button"
                className="action-pill"
                onClick={handleCopy}
                aria-label="Copy response"
                title="Copy to clipboard"
              >
                <CopyIcon size={14} />
                <span>Copy</span>
              </button>
            )}
            {onFollowUp && (
              <button
                type="button"
                className="action-pill"
                onClick={handleFollowUp}
                aria-label="Ask follow up"
                title="Ask follow up"
              >
                <span>Ask Follow-up</span>
              </button>
            )}
          </div>
        )}

        {/* Timestamp */}
        <div className="chat-card__time">{formatTime(message.timestamp)}</div>
      </div>
    </div>
  );
};

export default ChatMessage;
