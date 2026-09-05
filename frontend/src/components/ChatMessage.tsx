import React, { useCallback, useState } from "react";
import type { ChatMessage as ChatMessageType, LanguageCode } from "../types";
import { parseAnswer } from "../utils/parseAnswer";
import StructuredAnswer from "./StructuredAnswer";
import SourcesAccordion from "./SourcesAccordion";
import { SpeakerIcon, CopyIcon, ShieldCheckIcon } from "./Icons";

interface Props {
  message: ChatMessageType;
  onSpeak?: (id: string, text: string, language: LanguageCode) => void;
  isSpeaking?: boolean;
  onFollowUp?: (prompt: string) => void;
  onSimplify?: (prompt: string) => void;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

const ChatMessage: React.FC<Props> = ({
  message,
  onSpeak,
  isSpeaking = false,
  onFollowUp,
  onSimplify,
}) => {
  const isUser = message.role === "user";
  const hasSources = !isUser && message.sources && message.sources.length > 0;
  const [showSimplifyOptions, setShowSimplifyOptions] = useState<boolean>(false);

  // Parse structured sections for assistant messages
  const sections = !isUser ? parseAnswer(message.content) : null;

  const handleSpeakClick = useCallback(() => {
    if (onSpeak) onSpeak(message.id, message.content, message.language);
  }, [onSpeak, message.id, message.content, message.language]);

  const handleCopy = useCallback(() => {
    navigator.clipboard?.writeText(message.content).catch(() => {});
  }, [message.content]);

  const handleSimplifySelect = (mode: string) => {
    if (!onSimplify) return;
    let prompt = "";
    if (mode === "simple") {
      prompt = `Explain this in very simple language: "${message.content.slice(0, 150)}…"`;
    } else if (mode === "step") {
      prompt = `Break this down into numbered step-by-step actions: "${message.content.slice(0, 150)}…"`;
    } else if (mode === "example") {
      prompt = `Give a practical real-life example for a farmer/member explaining: "${message.content.slice(0, 150)}…"`;
    } else if (mode === "detailed") {
      prompt = `Explain the legal and technical clauses in detail for: "${message.content.slice(0, 150)}…"`;
    }
    onSimplify(prompt);
    setShowSimplifyOptions(false);
  };

  return (
    <div className={`chat-row chat-row--${message.role}`}>
      <div className="chat-card">
        {/* User Prompt or Assistant Response */}
        {isUser || !sections ? (
          <p className="chat-card__text">{message.content}</p>
        ) : (
          <StructuredAnswer sections={sections} />
        )}

        {/* Source / Grounding Badge */}
        {!isUser && (
          <div className="grounding-badge-row">
            {hasSources ? (
              <div className="grounded-tag grounded-tag--verified">
                <ShieldCheckIcon size={14} color="#2F855A" />
                <span>Source-backed guidance</span>
              </div>
            ) : (
              <div className="grounded-tag grounded-tag--reference">
                <span>Based on official information</span>
              </div>
            )}
          </div>
        )}

        {/* Source Drawer */}
        {hasSources && <SourcesAccordion sources={message.sources!} />}

        {/* Assistant Action Toolbar */}
        {!isUser && (
          <div className="chat-card__footer-toolbar">
            <div className="chat-card__actions">
              {onSpeak && (
                <button
                  type="button"
                  className={`action-btn ${isSpeaking ? "action-btn--active" : ""}`}
                  onClick={handleSpeakClick}
                  aria-label={isSpeaking ? "Stop reading" : "Read aloud"}
                >
                  <SpeakerIcon size={14} />
                  <span>{isSpeaking ? "Stop" : "Read Aloud"}</span>
                </button>
              )}
              {navigator.clipboard && (
                <button
                  type="button"
                  className="action-btn"
                  onClick={handleCopy}
                  aria-label="Copy response"
                >
                  <CopyIcon size={14} />
                  <span>Copy</span>
                </button>
              )}
              {onFollowUp && (
                <button
                  type="button"
                  className="action-btn"
                  onClick={() => onFollowUp("Can you provide more details about this service?")}
                  aria-label="Ask follow up"
                >
                  <span>Ask Follow-up</span>
                </button>
              )}
              {onSimplify && (
                <button
                  type="button"
                  className="action-btn action-btn--accent"
                  onClick={() => setShowSimplifyOptions((s) => !s)}
                >
                  <span>Explain This…</span>
                </button>
              )}
            </div>

            {/* Simplify Options Sub-bar */}
            {showSimplifyOptions && (
              <div className="simplify-bar">
                <span className="simplify-bar__label">Explain as:</span>
                <button
                  type="button"
                  className="simplify-btn"
                  onClick={() => handleSimplifySelect("simple")}
                >
                  Simple
                </button>
                <button
                  type="button"
                  className="simplify-btn"
                  onClick={() => handleSimplifySelect("step")}
                >
                  Step-by-step
                </button>
                <button
                  type="button"
                  className="simplify-btn"
                  onClick={() => handleSimplifySelect("example")}
                >
                  Example
                </button>
                <button
                  type="button"
                  className="simplify-btn"
                  onClick={() => handleSimplifySelect("detailed")}
                >
                  Detailed
                </button>
              </div>
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
