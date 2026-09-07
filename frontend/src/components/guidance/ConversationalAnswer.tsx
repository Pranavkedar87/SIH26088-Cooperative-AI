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

  // Parse content line-by-line into proper semantic blocks (headings, lists, paragraphs)
  const lines = cleanContent.split("\n").map((l) => l.trim());
  interface SectionBlock {
    type: "heading" | "bullet_list" | "numbered_list" | "paragraph";
    items: string[];
  }
  const parsedBlocks: SectionBlock[] = [];
  let currentBlock: SectionBlock | null = null;

  for (const line of lines) {
    if (!line) {
      if (currentBlock) {
        parsedBlocks.push(currentBlock);
        currentBlock = null;
      }
      continue;
    }

    if (line.startsWith("#")) {
      if (currentBlock) parsedBlocks.push(currentBlock);
      parsedBlocks.push({ type: "heading", items: [line.replace(/^#+\s*/, "")] });
      currentBlock = null;
    } else if (/^[-*•]\s+/.test(line)) {
      const itemText = line.replace(/^[-*•]\s+/, "");
      if (currentBlock && currentBlock.type === "bullet_list") {
        currentBlock.items.push(itemText);
      } else {
        if (currentBlock) parsedBlocks.push(currentBlock);
        currentBlock = { type: "bullet_list", items: [itemText] };
      }
    } else if (/^\d+\.\s+/.test(line)) {
      const itemText = line.replace(/^\d+\.\s+/, "");
      if (currentBlock && currentBlock.type === "numbered_list") {
        currentBlock.items.push(itemText);
      } else {
        if (currentBlock) parsedBlocks.push(currentBlock);
        currentBlock = { type: "numbered_list", items: [itemText] };
      }
    } else {
      if (currentBlock && currentBlock.type === "paragraph") {
        currentBlock.items.push(line);
      } else {
        if (currentBlock) parsedBlocks.push(currentBlock);
        currentBlock = { type: "paragraph", items: [line] };
      }
    }
  }
  if (currentBlock) parsedBlocks.push(currentBlock);

  const isOfflineFallback =
    /unable to reach the assistance service|सहाय्य सेवेशी संपर्क साधू शकत नाही|सहायता सेवा से संपर्क नहीं कर पा रहा/i.test(content);

  return (
    <div className="conversational-answer-container" data-focus={effectiveFocus}>
      {/* Domain Badge Tag */}
      {guidance.domainLabel && !isOfflineFallback && (
        <AnswerSummary
          summary=""
          domainLabel={guidance.domainLabel}
          language={language}
        />
      )}

      {/* Main Conversational Markdown Body */}
      <div className="conversational-body">
        {parsedBlocks.map((block, bIdx) => {
          if (block.type === "heading") {
            return (
              <h3 key={bIdx} className="conversational-heading">
                {renderFormattedText(block.items[0])}
              </h3>
            );
          }

          if (block.type === "bullet_list") {
            return (
              <ul key={bIdx} className="conversational-ul">
                {block.items.map((item, iIdx) => (
                  <li key={iIdx}>{renderFormattedText(item)}</li>
                ))}
              </ul>
            );
          }

          if (block.type === "numbered_list") {
            return (
              <ol key={bIdx} className="conversational-ol">
                {block.items.map((item, iIdx) => (
                  <li key={iIdx}>{renderFormattedText(item)}</li>
                ))}
              </ol>
            );
          }

          return (
            <p key={bIdx} className="conversational-p">
              {renderFormattedText(block.items.join(" "))}
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

      {/* Suggested Follow-up Action Chips (Only for genuine responses) */}
      {!isOfflineFallback && (
        <NextStepCard
          actions={getContextualActions(guidance.domain, language, effectiveFocus)}
          onExecuteAction={onExecuteAction}
          language={language}
        />
      )}
    </div>
  );
};

export default ConversationalAnswer;
