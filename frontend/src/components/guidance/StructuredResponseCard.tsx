import React, { useState } from "react";
import type {
  LanguageCode,
  StructuredAnswerData,
  AnswerSection,
  SourceItem,
  SuggestedFollowup,
} from "../../types";
import { useTranslation } from "../../i18n";
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

function renderParagraphs(text: string): React.ReactNode[] {
  if (!text) return [];
  const blocks = text.split(/\n\n+/);
  return blocks.map((block, idx) => {
    const trimmed = block.trim();
    if (!trimmed) return null;
    return (
      <p key={idx} className="conversational-p">
        {renderFormattedText(trimmed)}
      </p>
    );
  });
}

export const StructuredResponseCard: React.FC<Props> = ({
  data,
  language = "mr",
  onExecuteAction,
  sources = [],
  suggestedFollowups = [],
}) => {
  const t = useTranslation(language);
  const [expandedDetails, setExpandedDetails] = useState<Record<number, boolean>>({});

  const toggleDetail = (idx: number) => {
    setExpandedDetails((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const followups =
    suggestedFollowups.length > 0
      ? suggestedFollowups
      : data.suggested_followups && data.suggested_followups.length > 0
      ? data.suggested_followups
      : [];

  const effectiveSources =
    sources.length > 0
      ? sources
      : data.sources && data.sources.length > 0
      ? data.sources
      : [];

  return (
    <div className="structured-response-container">
      {/* 1. PRIMARY CONVERSATIONAL DIRECT ANSWER */}
      {data.direct_answer && (
        <div className="conversational-body structured-conversational-body">
          {renderParagraphs(data.direct_answer)}
        </div>
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
      {effectiveSources && effectiveSources.length > 0 && (
        <div className="conversational-sources-block">
          <div className="conversational-sources-title">
            <ShieldCheckIcon size={13} color="#0F6B68" />
            <span>
              {t("sources.officialSources")}
            </span>
          </div>
          <div className="conversational-sources-chips">
            {effectiveSources.map((src, i) => (
              <span key={i} className="conversational-source-chip" style={{ display: 'inline-flex', flexDirection: 'column', gap: '4px', padding: '6px 10px', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                  <span>{src.title}</span>
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
                </div>
                {(src.authority_level || src.jurisdiction || src.currentness_status || src.verification_status) && (
                  <div style={{ fontSize: '10px', opacity: 0.85, display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '2px' }}>
                    {src.authority_level && src.authority_level !== "UNKNOWN" && (
                      <span style={{ background: '#eef2f6', padding: '1px 5px', borderRadius: '3px' }}>
                        🏛️ {src.authority_level.replace(/_/g, ' ')}
                      </span>
                    )}
                    {src.jurisdiction && src.jurisdiction !== "UNKNOWN" && (
                      <span style={{ background: '#eef2f6', padding: '1px 5px', borderRadius: '3px' }}>
                        📍 {src.jurisdiction}
                      </span>
                    )}
                    {src.currentness_status && (
                      <span style={{
                        background: src.currentness_status === 'ACTIVE_IN_FORCE' ? '#e6f4ea' : '#fef7e0',
                        color: src.currentness_status === 'ACTIVE_IN_FORCE' ? '#137333' : '#b06000',
                        padding: '1px 5px',
                        borderRadius: '3px',
                        fontWeight: 500
                      }}>
                        ⏱️ {src.currentness_status === 'ACTIVE_IN_FORCE' ? 'In Force' : (src.currentness_status === 'NEEDS_VERIFICATION' ? 'Currency Unconfirmed' : src.currentness_status)}
                      </span>
                    )}
                    {src.verification_status && (
                      <span style={{
                        background: src.verification_status === 'VERIFIED_OFFICIAL' ? '#e6f4ea' : '#fef7e0',
                        color: src.verification_status === 'VERIFIED_OFFICIAL' ? '#137333' : '#b06000',
                        padding: '1px 5px',
                        borderRadius: '3px',
                        fontWeight: 500
                      }}>
                        🛡️ {src.verification_status === 'VERIFIED_OFFICIAL' ? 'Verified Official' : (src.verification_status === 'OFFICIAL_NEEDS_VERIFICATION' ? 'Official (Needs Verification)' : 'Needs Verification')}
                      </span>
                    )}
                  </div>
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
            {t("guidance.youCanAskNext")}
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
