import React, { useCallback, useState } from "react";
import type { ChatMessage as ChatMessageType, LanguageCode } from "../types";
import GuidanceRenderer from "./guidance/GuidanceRenderer";
import SourcesAccordion from "./SourcesAccordion";
import { generateGuidancePdf } from "../utils/pdfGenerator";
import { parseGuidance } from "../utils/guidanceParser";
import { SpeakerIcon, PauseIcon, CopyIcon, ShieldCheckIcon, DownloadIcon } from "./Icons";

interface Props {
  message: ChatMessageType;
  userQuestion?: string;
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
  userQuestion,
  onSpeak,
  isSpeaking = false,
  onFollowUp,
  onSimplify: _onSimplify,
}) => {
  const isUser = message.role === "user";
  const hasSources = !isUser && message.sources && message.sources.length > 0;
  const [isGeneratingPdf, setIsGeneratingPdf] = useState<boolean>(false);

  const handleSpeakClick = useCallback(() => {
    if (onSpeak) onSpeak(message.id, message.content, message.language);
  }, [onSpeak, message.id, message.content, message.language]);

  const handleCopy = useCallback(() => {
    navigator.clipboard?.writeText(message.content).catch(() => {});
  }, [message.content]);

  const handleDownloadPdf = async () => {
    try {
      setIsGeneratingPdf(true);
      const parsed = parseGuidance(message.content, message.language);
      await generateGuidancePdf({
        question: userQuestion,
        language: message.language,
        domainLabel: parsed.domainLabel,
        summary: parsed.summary,
        keyFacts: parsed.keyFacts,
        steps: parsed.steps,
        warnings: parsed.warnings,
        nextSteps: parsed.nextSteps,
        sources: message.sources?.map((s) => ({
          title: s.title,
          authority: s.source_name || undefined,
          url: s.source_url || undefined,
        })),
      });
    } catch (err) {
      console.error("PDF download error:", err);
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  const pdfBtnLabel = isGeneratingPdf
    ? message.language === "hi"
      ? "पीडीएफ बन रहा है..."
      : message.language === "en"
      ? "Generating PDF..."
      : "PDF तयार होत आहे..."
    : message.language === "hi"
    ? "मार्गदर्शन PDF डाउनलोड करें"
    : message.language === "en"
    ? "Download Guidance PDF"
    : "मार्गदर्शन PDF डाउनलोड करा";

  const speakBtnLabel = isSpeaking
    ? message.language === "hi"
      ? "रोकें"
      : message.language === "en"
      ? "Stop"
      : "थांबवा"
    : message.language === "hi"
    ? "सुनें"
    : message.language === "en"
    ? "Read Aloud"
    : "ऐकून घ्या";

  return (
    <div className={`chat-row chat-row--${message.role}`}>
      <div className="chat-card">
        {/* User Prompt or Assistant Guidance Renderer */}
        {isUser ? (
          <p className="chat-card__text">{message.content}</p>
        ) : (
          <GuidanceRenderer
            rawContent={message.content}
            userQuestion={userQuestion}
            language={message.language}
            answerFocus={message.answer_focus}
            onExecuteAction={onFollowUp}
            sources={message.sources}
          />
        )}

        {/* Source / Grounding Badge */}
        {!isUser && (
          <div className="grounding-badge-row">
            {hasSources ? (
              <div className="grounded-tag grounded-tag--verified">
                <ShieldCheckIcon size={14} color="#238477" />
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
              {/* Primary Action: Download Guidance PDF */}
              <button
                type="button"
                className="action-btn action-btn--primary"
                onClick={handleDownloadPdf}
                disabled={isGeneratingPdf}
                aria-label="Download guidance PDF"
              >
                <DownloadIcon size={14} color="#FFFFFF" />
                <span>{pdfBtnLabel}</span>
              </button>

              {/* Voice Read Aloud CTA */}
              {onSpeak && (
                <button
                  type="button"
                  className={`action-btn ${isSpeaking ? "action-btn--active" : ""}`}
                  onClick={handleSpeakClick}
                  aria-label={isSpeaking ? "Stop reading" : "Read aloud"}
                >
                  {isSpeaking ? <PauseIcon size={14} /> : <SpeakerIcon size={14} />}
                  <span>{speakBtnLabel}</span>
                </button>
              )}

              {/* Copy CTA */}
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
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className="chat-card__time">{formatTime(message.timestamp)}</div>
      </div>
    </div>
  );
};

export default ChatMessage;
