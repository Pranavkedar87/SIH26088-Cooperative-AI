import React, { useState, useEffect, useRef } from "react";
import type { LanguageCode, VisionAnalyzeResponse, DocumentType, ReadabilityStatus } from "../types";
import { useTranslation } from "../i18n";
import {
  FileTextIcon,
  CheckCircleIcon,
  AlertTriangleIcon,
  XIcon,
  RotateCcwIcon,
  SendIcon,
  ShieldCheckIcon,
  InfoIcon,
} from "./Icons";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  result: VisionAnalyzeResponse;
  language: LanguageCode;
  previewUrl?: string | null;
  onSelectQuestion: (question: string) => void;
  onRetake: () => void;
}

export const DocumentAnalysisModal: React.FC<Props> = ({
  isOpen,
  onClose,
  result,
  language,
  previewUrl,
  onSelectQuestion,
  onRetake,
}) => {
  const t = useTranslation(language);
  const [customQuestion, setCustomQuestion] = useState("");
  const [showPreview, setShowPreview] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

  // Focus trap / ESC to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const isIdentity = result.document_type === "IDENTITY_DOCUMENT";
  const isClear = result.readability === "CLEAR";

  const getDocTypeLabel = (type: DocumentType): string => {
    const key = `docAnalysis.type.${type}`;
    const translated = t(key);
    return translated !== key ? translated : type;
  };

  const getReadabilityLabel = (readability: ReadabilityStatus): string => {
    const key = `docAnalysis.readability.${readability}`;
    const translated = t(key);
    return translated !== key ? translated : readability;
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = customQuestion.trim();
    if (!trimmed) return;
    onSelectQuestion(trimmed);
  };

  const handleChipClick = (question: string) => {
    onSelectQuestion(question);
  };

  return (
    <div
      className="doc-analysis-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="doc-analysis-title"
      ref={modalRef}
    >
      <div className="doc-analysis-card">
        {/* Header */}
        <div className="doc-analysis-header">
          <div className="doc-analysis-header-title-wrap">
            <div className="doc-analysis-icon-box">
              <FileTextIcon size={22} color="#0F6B68" />
            </div>
            <div>
              <h2 id="doc-analysis-title" className="doc-analysis-title">
                {t("docAnalysis.title")}
              </h2>
              <span className="doc-analysis-subtitle">
                {t("docAnalysis.subtitle")}
              </span>
            </div>
          </div>
          <button
            type="button"
            className="doc-analysis-close-btn"
            onClick={onClose}
            aria-label={t("docAnalysis.close")}
          >
            <XIcon size={18} color="#68757D" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="doc-analysis-body">
          {/* Trust Boundary Banner: AI Document Extraction Notice */}
          <div className="doc-analysis-trust-banner" role="note">
            <span className="doc-analysis-trust-badge">DOCUMENT INFORMATION</span>
            <span className="doc-analysis-trust-text">
              {t("docAnalysis.referenceNotice")}
            </span>
          </div>

          {/* Document Identified & Readability Badges */}
          <div className="doc-analysis-meta-row">
            <div className="doc-analysis-type-badge">
              <span className="doc-analysis-meta-label">{t("docAnalysis.identified")}</span>
              <strong className="doc-analysis-meta-value">{getDocTypeLabel(result.document_type)}</strong>
            </div>

            <div
              className={`doc-analysis-readability-badge doc-analysis-readability--${result.readability.toLowerCase()}`}
            >
              {isClear ? (
                <CheckCircleIcon size={16} color="#0F6B68" />
              ) : (
                <AlertTriangleIcon size={16} color="#B94A48" />
              )}
              <span>{getReadabilityLabel(result.readability)}</span>
            </div>
          </div>

          {/* Optional Image Preview Accordion */}
          {previewUrl && (
            <div className="doc-analysis-preview-section">
              <button
                type="button"
                className="doc-analysis-preview-toggle"
                onClick={() => setShowPreview((prev) => !prev)}
                aria-expanded={showPreview}
              >
                <span>{t("docAnalysis.previewToggle")}</span>
                <span className="doc-analysis-preview-arrow">{showPreview ? "▲" : "▼"}</span>
              </button>
              {showPreview && (
                <div className="doc-analysis-preview-img-wrap">
                  <img
                    src={previewUrl}
                    alt="Document preview"
                    className="doc-analysis-preview-img"
                  />
                </div>
              )}
            </div>
          )}

          {/* Readability Retake Warning */}
          {!isClear && (
            <div className="doc-analysis-warning-box" role="alert">
              <AlertTriangleIcon size={18} color="#B94A48" />
              <div className="doc-analysis-warning-content">
                <p className="doc-analysis-warning-text">{t("docAnalysis.retakeWarning")}</p>
                <button
                  type="button"
                  className="doc-analysis-warning-retake-btn"
                  onClick={onRetake}
                >
                  <RotateCcwIcon size={14} color="#B94A48" />
                  <span>{t("docAnalysis.retake")}</span>
                </button>
              </div>
            </div>
          )}

          {/* CASE 1: IDENTITY DOCUMENT REFUSAL */}
          {isIdentity ? (
            <div className="doc-analysis-refusal-card" role="alert">
              <div className="doc-analysis-refusal-header">
                <ShieldCheckIcon size={24} color="#0F6B68" />
                <h3 className="doc-analysis-refusal-title">
                  {t("docAnalysis.identityRefusalTitle")}
                </h3>
              </div>
              <p className="doc-analysis-refusal-reason">
                {result.refusal_reason || t("docAnalysis.identityExplanation")}
              </p>
              <div className="doc-analysis-refusal-action">
                <button
                  type="button"
                  className="doc-analysis-btn-primary"
                  onClick={onRetake}
                >
                  <RotateCcwIcon size={16} color="#FFFFFF" />
                  <span>{t("docAnalysis.scanAnother")}</span>
                </button>
              </div>
            </div>
          ) : (
            /* CASE 2: REGULAR SUPPORTED DOCUMENT */
            <>
              {/* Document Summary */}
              {result.document_summary && (
                <div className="doc-analysis-section">
                  <h3 className="doc-analysis-section-title">
                    {t("docAnalysis.summaryTitle")}
                  </h3>
                  <div className="doc-analysis-summary-box">
                    <p className="doc-analysis-summary-text">{result.document_summary}</p>
                    <span className="doc-analysis-disclaimer">
                      {t("docAnalysis.summaryDisclaimer")}
                    </span>
                  </div>
                </div>
              )}

              {/* PII Masking Gentle Alert */}
              {result.has_sensitive_pii && (
                <div className="doc-analysis-pii-alert" role="status">
                  <InfoIcon size={16} color="#123B5D" />
                  <span>{t("docAnalysis.piiNotice")}</span>
                </div>
              )}

              {/* Key Extracted Details */}
              {result.key_fields && Object.keys(result.key_fields).length > 0 && (
                <div className="doc-analysis-section">
                  <div className="doc-analysis-section-header-wrap">
                    <h3 className="doc-analysis-section-title">
                      {t("docAnalysis.keyFieldsTitle")}
                    </h3>
                    <span className="doc-analysis-section-sub">
                      {t("docAnalysis.extractedFromDoc")}
                    </span>
                  </div>

                  <div className="doc-analysis-fields-table">
                    {Object.entries(result.key_fields).map(([rawKey, val]) => {
                      const formattedKey = rawKey
                        .replace(/_/g, " ")
                        .replace(/\b\w/g, (c) => c.toUpperCase());
                      return (
                        <div key={rawKey} className="doc-analysis-field-row">
                          <span className="doc-analysis-field-key">{formattedKey}</span>
                          <span className="doc-analysis-field-value">
                            {val ? String(val) : "—"}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Suggested Questions */}
              {result.suggested_questions && result.suggested_questions.length > 0 && (
                <div className="doc-analysis-section">
                  <h3 className="doc-analysis-section-title">
                    {t("docAnalysis.questionsTitle")}
                  </h3>
                  <div className="doc-analysis-chips-grid">
                    {result.suggested_questions.map((q, idx) => (
                      <button
                        key={idx}
                        type="button"
                        className="doc-analysis-chip"
                        onClick={() => handleChipClick(q)}
                      >
                        <span>{q}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Custom Question Form */}
              <div className="doc-analysis-section">
                <h3 className="doc-analysis-section-title">
                  {t("docAnalysis.customQuestionTitle")}
                </h3>
                <form onSubmit={handleCustomSubmit} className="doc-analysis-custom-form">
                  <input
                    type="text"
                    className="doc-analysis-input"
                    value={customQuestion}
                    onChange={(e) => setCustomQuestion(e.target.value)}
                    placeholder={t("docAnalysis.customQuestionPlaceholder")}
                    aria-label={t("docAnalysis.customQuestionTitle")}
                  />
                  <button
                    type="submit"
                    className="doc-analysis-btn-ask"
                    disabled={!customQuestion.trim()}
                  >
                    <SendIcon size={16} color="#FFFFFF" />
                    <span>{t("docAnalysis.askButton")}</span>
                  </button>
                </form>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="doc-analysis-footer">
          <button
            type="button"
            className="doc-analysis-btn-secondary"
            onClick={onRetake}
          >
            <RotateCcwIcon size={16} color="#0F6B68" />
            <span>{t("docAnalysis.retake")}</span>
          </button>
          <button
            type="button"
            className="doc-analysis-btn-close"
            onClick={onClose}
          >
            {t("docAnalysis.close")}
          </button>
        </div>
      </div>
    </div>
  );
};
