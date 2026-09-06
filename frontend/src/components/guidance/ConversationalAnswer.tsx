import React from "react";
import type { LanguageCode, SourceItem } from "../../types";
import { getContextualActions, parseGuidance } from "../../utils/guidanceParser";
import AnswerSummary from "./AnswerSummary";
import NextStepCard from "./NextStepCard";
import { ShieldCheckIcon, ExternalLinkIcon } from "../Icons";

interface Props {
  content: string;
  language?: LanguageCode;
  answerFocus?: string;
  onExecuteAction?: (query: string) => void;
  sources?: SourceItem[];
}

function renderFormattedText(text: string): React.ReactNode[] {
  if (!text) return [];
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g;
  let lastIdx = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.substring(lastIdx, match.index));
    }
    const token = match[0];
    if (token.startsWith("**") && token.endsWith("**")) {
      parts.push(<strong key={match.index}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("[")) {
      const closingBracket = token.indexOf("]");
      const label = token.slice(1, closingBracket);
      const url = token.slice(closingBracket + 2, -1);
      parts.push(
        <a
          key={match.index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="conversational-link"
        >
          {label} ↗
        </a>
      );
    }
    lastIdx = regex.lastIndex;
  }
  if (lastIdx < text.length) {
    parts.push(text.substring(lastIdx));
  }
  return parts;
}

export const ConversationalAnswer: React.FC<Props> = ({
  content,
  language = "mr",
  answerFocus,
  onExecuteAction,
  sources = [],
}) => {
  if (!content || !content.trim()) return null;

  const guidance = parseGuidance(content, language, answerFocus);
  const effectiveFocus = (guidance.answerFocus || answerFocus || "OVERVIEW").toUpperCase();

  // Strip generic legacy header prefixes
  const cleanContent = content
    .replace(/^### Official Guidance\s*/i, "")
    .replace(/^COOPERATIVE GUIDANCE\s*/i, "")
    .replace(/^What Should I Do Now:?\s*/i, "")
    .trim();

  const blocks = cleanContent.split(/\n\n+/);

  return (
    <div className="conversational-answer-container" data-focus={effectiveFocus}>
      {/* Domain Badge Tag */}
      {guidance.domainLabel && (
        <AnswerSummary
          summary=""
          domainLabel={guidance.domainLabel}
          language={language}
        />
      )}

      {/* Main Conversational Markdown Body */}
      <div className="conversational-body">
        {blocks.map((block, bIdx) => {
          const trimmed = block.trim();
          if (!trimmed) return null;

          // Headings ###
          if (trimmed.startsWith("#")) {
            const headingText = trimmed.replace(/^#+\s*/, "");
            return (
              <h3 key={bIdx} className="conversational-heading">
                {renderFormattedText(headingText)}
              </h3>
            );
          }

          const lines = trimmed.split("\n").map((l) => l.trim()).filter(Boolean);
          const isNumberedList = lines.length > 0 && lines.every((l) => /^\d+\.\s+/.test(l));
          const isBulletList = lines.length > 0 && lines.every((l) => /^[-*•]\s+/.test(l));

          // Ordered List (Numbered steps)
          if (isNumberedList) {
            return (
              <ol key={bIdx} className="conversational-ol">
                {lines.map((line, lIdx) => {
                  const itemText = line.replace(/^\d+\.\s+/, "");
                  return <li key={lIdx}>{renderFormattedText(itemText)}</li>;
                })}
              </ol>
            );
          }

          // Unordered List (Bullet points)
          if (isBulletList) {
            return (
              <ul key={bIdx} className="conversational-ul">
                {lines.map((line, lIdx) => {
                  const itemText = line.replace(/^[-*•]\s+/, "");
                  return <li key={lIdx}>{renderFormattedText(itemText)}</li>;
                })}
              </ul>
            );
          }

          // Paragraph
          return (
            <p key={bIdx} className="conversational-p">
              {renderFormattedText(trimmed)}
            </p>
          );
        })}
      </div>

      {/* Compact Official Sources List */}
      {sources && sources.length > 0 && (
        <div className="conversational-sources-block">
          <div className="conversational-sources-title">
            <ShieldCheckIcon size={13} color="#126B62" />
            <span>
              {language === "hi"
                ? "अधिकृत स्रोत एवं संदर्भ:"
                : language === "en"
                ? "Official Sources & References:"
                : "अधिकृत स्रोत व संदर्भ:"}
            </span>
          </div>
          <div className="conversational-sources-chips">
            {sources.map((src, i) => (
              <span key={i} className="conversational-source-chip">
                {src.title}
                {src.source_url && (
                  <a
                    href={src.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="conversational-source-link"
                  >
                    <ExternalLinkIcon size={11} color="#126B62" />
                  </a>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Suggested Follow-up Action Chips */}
      <NextStepCard
        actions={getContextualActions(guidance.domain, language, effectiveFocus)}
        onExecuteAction={onExecuteAction}
        language={language}
      />
    </div>
  );
};

export default ConversationalAnswer;
