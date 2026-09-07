import React, { useState } from "react";
import type {
  LanguageCode,
  StructuredAnswerData,
  AnswerSection,
  SourceItem,
  SuggestedFollowup,
} from "../../types";
import {
  ShieldCheckIcon,
  ExternalLinkIcon,
  FileCheckIcon,
  LandmarkIcon,
  ChevronRightIcon,
  InfoIcon,
} from "../Icons";

interface Props {
  data: StructuredAnswerData;
  language?: LanguageCode;
  onExecuteAction?: (query: string) => void;
  sources?: SourceItem[];
  suggestedFollowups?: SuggestedFollowup[];
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

const DIRECT_LABEL: Record<string, string> = {
  mr: "थोडक्यात उत्तर",
  hi: "सीधा जवाब",
  en: "Direct Answer",
  gu: "સીધો જવાબ",
  ta: "நேரடி பதில்",
  bn: "সরাসরি উত্তর",
};

export const StructuredResponseCard: React.FC<Props> = ({
  data,
  language = "mr",
  onExecuteAction,
  sources = [],
  suggestedFollowups = [],
}) => {
  const [expandedDetails, setExpandedDetails] = useState<Record<number, boolean>>({});

  const toggleDetail = (idx: number) => {
    setExpandedDetails((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const directLabel = DIRECT_LABEL[language] ?? DIRECT_LABEL.en;
  const followups =
    suggestedFollowups.length > 0
      ? suggestedFollowups
      : data.suggested_followups && data.suggested_followups.length > 0
      ? data.suggested_followups
      : [];

  return (
    <div className="structured-response-container">
      {/* 1. DIRECT ANSWER HIGHLIGHT CARD */}
      {data.direct_answer && (
        <section className="structured-direct-answer" aria-label={directLabel}>
          <div className="structured-direct-badge">
            <span className="direct-badge-dot" />
            <span className="direct-badge-title">{directLabel}</span>
          </div>
          <div className="structured-direct-content">
            {renderFormattedText(data.direct_answer)}
          </div>
        </section>
      )}

      {/* 2. DYNAMIC SECTIONS RENDERER */}
      {data.sections && data.sections.length > 0 && (
        <div className="structured-sections-flow">
          {data.sections.map((section: AnswerSection, sIdx: number) => {
            const secType = (section.type || "info").toLowerCase();

            // SECTION TYPE: KEY FACTS (Cards / Stat Badges)
            if (secType === "key_facts" && section.items && section.items.length > 0) {
              return (
                <div key={sIdx} className="structured-section structured-section--facts">
                  {section.title && (
                    <h4 className="structured-section-title">
                      <span className="section-title-bullet">◆</span>
                      <span>{section.title}</span>
                    </h4>
                  )}
                  <div className="key-facts-grid">
                    {section.items.map((item, fIdx) => (
                      <div key={fIdx} className="key-fact-card">
                        {item.label && <div className="key-fact-label">{item.label}</div>}
                        <div className="key-fact-value">
                          {renderFormattedText(item.value || item.title || item.content || "")}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            }

            // SECTION TYPE: STEPS (Numbered Step-by-Step Action Cards)
            if (secType === "steps" && section.items && section.items.length > 0) {
              return (
                <div key={sIdx} className="structured-section structured-section--steps">
                  {section.title && (
                    <h4 className="structured-section-title">
                      <span className="section-title-bullet">◆</span>
                      <span>{section.title}</span>
                    </h4>
                  )}
                  <div className="action-steps-list">
                    {section.items.map((step, stepIdx) => (
                      <div key={stepIdx} className="action-step-card">
                        <div className="step-badge">{String(stepIdx + 1).padStart(2, "0")}</div>
                        <div className="step-body">
                          {step.title && (
                            <div className="step-title">
                              {renderFormattedText(step.title.replace(/^[-*•\d+\.]\s*/, ""))}
                            </div>
                          )}
                          {step.description && (
                            <div className="step-desc">
                              {renderFormattedText(step.description)}
                            </div>
                          )}
                          {!step.title && step.content && (
                            <div className="step-desc">
                              {renderFormattedText(step.content)}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            }

            // SECTION TYPE: DOCUMENTS (Checklist of Requirements)
            if (secType === "documents" && section.items && section.items.length > 0) {
              return (
                <div key={sIdx} className="structured-section structured-section--documents">
                  {section.title && (
                    <h4 className="structured-section-title">
                      <FileCheckIcon size={16} color="#0F6B68" />
                      <span>{section.title}</span>
                    </h4>
                  )}
                  <div className="documents-checklist">
                    {section.items.map((doc, docIdx) => (
                      <div key={docIdx} className="document-item-card">
                        <div className="doc-checkbox-icon">
                          <span className="doc-check-box" />
                        </div>
                        <div className="doc-item-body">
                          <span className="doc-name">
                            {renderFormattedText(doc.name || doc.title || "")}
                          </span>
                          {doc.description && (
                            <span className="doc-desc">
                              {renderFormattedText(doc.description)}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            }

            // SECTION TYPE: WHERE TO GO / WHERE TO APPLY
            if (secType === "where_to_go" && section.items && section.items.length > 0) {
              return (
                <div key={sIdx} className="structured-section structured-section--channels">
                  {section.title && (
                    <h4 className="structured-section-title">
                      <LandmarkIcon size={16} color="#0F6B68" />
                      <span>{section.title}</span>
                    </h4>
                  )}
                  <div className="channels-grid">
                    {section.items.map((ch, chIdx) => (
                      <div key={chIdx} className="channel-card">
                        <div className="channel-title">
                          {renderFormattedText(ch.name || ch.title || "")}
                        </div>
                        {(ch.description || ch.content) && (
                          <div className="channel-desc">
                            {renderFormattedText(ch.description || ch.content || "")}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            }

            // SECTION TYPE: NEXT ACTION (Highlight Action Recommendation)
            if (secType === "next_action" && (section.content || (section.items && section.items.length > 0))) {
              const textContent =
                section.content ||
                section.items?.map((i) => i.content || i.title || i.description).filter(Boolean).join(". ");
              return (
                <div key={sIdx} className="structured-section structured-section--next-action">
                  <div className="next-action-box">
                    <div className="next-action-header">
                      <span className="next-action-indicator">➔</span>
                      <span className="next-action-heading">{section.title || "Next Step"}</span>
                    </div>
                    <div className="next-action-text">{renderFormattedText(textContent || "")}</div>
                  </div>
                </div>
              );
            }

            // SECTION TYPE: DETAILS (Collapsible / Full Detail Context)
            if (secType === "details" && section.content) {
              const isExpanded = expandedDetails[sIdx] ?? false;
              return (
                <div key={sIdx} className="structured-section structured-section--details">
                  <button
                    type="button"
                    className="details-toggle-btn"
                    onClick={() => toggleDetail(sIdx)}
                    aria-expanded={isExpanded}
                  >
                    <div className="details-toggle-left">
                      <InfoIcon size={15} color="#0F6B68" />
                      <span>{section.title || "Detailed Information"}</span>
                    </div>
                    <span className={`details-toggle-arrow ${isExpanded ? "details-toggle-arrow--open" : ""}`}>
                      ▼
                    </span>
                  </button>
                  {isExpanded && (
                    <div className="details-expanded-body">
                      {renderFormattedText(section.content)}
                    </div>
                  )}
                </div>
              );
            }

            // SECTION TYPE: GENERAL INFO FALLBACK
            return (
              <div key={sIdx} className="structured-section structured-section--general">
                {section.title && <h4 className="structured-section-title">{section.title}</h4>}
                {section.content && <p className="section-general-text">{renderFormattedText(section.content)}</p>}
                {section.items && section.items.length > 0 && (
                  <ul className="section-general-list">
                    {section.items.map((it, iIdx) => (
                      <li key={iIdx}>
                        {it.title && <strong>{it.title}: </strong>}
                        {renderFormattedText(it.description || it.content || "")}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* 3. VERIFIED OFFICIAL SOURCES CHIPS */}
      {sources && sources.length > 0 && (
        <div className="conversational-sources-block">
          <div className="conversational-sources-title">
            <ShieldCheckIcon size={13} color="#0F6B68" />
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
                    <ExternalLinkIcon size={11} color="#0F6B68" />
                  </a>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 4. CONTEXTUAL SUGGESTED FOLLOW-UP CHIPS */}
      {followups && followups.length > 0 && onExecuteAction && (
        <div className="structured-followups-block">
          <div className="structured-followups-label">
            {language === "hi"
              ? "आप आगे यह पूछ सकते हैं:"
              : language === "en"
              ? "You can ask next:"
              : "तुम्ही पुढे हे विचारू शकता:"}
          </div>
          <div className="structured-followups-grid">
            {followups.map((item, idx) => (
              <button
                key={idx}
                type="button"
                className="structured-followup-chip"
                onClick={() => onExecuteAction(item.query || item.label)}
              >
                <span>{item.label}</span>
                <ChevronRightIcon size={13} color="#0F6B68" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default StructuredResponseCard;
