import React, { useState, useEffect, useCallback } from "react";
import type { LanguageCode, SourceItem, HumanHandoffResponse } from "../types";
import { useTranslation } from "../i18n";
import { submitHumanHandoff } from "../api/client";
import {
  LandmarkIcon,
  XIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  AlertTriangleIcon,
  CopyIcon,
  CheckIcon,
  FileTextIcon,
  InfoIcon,
} from "./Icons";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  language: LanguageCode;
  initialQuery?: string;
  initialGuidance?: string;
  initialCitations?: SourceItem[];
  conversationId?: string | null;
  category?: string;
}

type SubmissionState = "READY" | "SUBMITTING" | "SUCCESS" | "ERROR";

export const HandoffModal: React.FC<Props> = ({
  isOpen,
  onClose,
  language,
  initialQuery = "",
  initialGuidance = "",
  initialCitations = [],
  conversationId = null,
  category = "PACS_SERVICE",
}) => {
  const t = useTranslation(language);

  // Form Fields
  const [citizenName, setCitizenName] = useState<string>("");
  const [citizenPhone, setCitizenPhone] = useState<string>("");
  const [pacsName, setPacsName] = useState<string>("");
  const [village, setVillage] = useState<string>("");
  const [officerLanguage, setOfficerLanguage] = useState<string>(() => {
    // Intelligent default: if citizen is in Marathi or Hindi, officer language defaults to English (or vice versa)
    return language === "en" ? "mr" : "en";
  });
  const [issueSummary, setIssueSummary] = useState<string>(initialQuery);

  // Submission State
  const [state, setState] = useState<SubmissionState>("READY");
  const [response, setResponse] = useState<HumanHandoffResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [codeCopied, setCodeCopied] = useState<boolean>(false);

  // Sync initial query when opened
  useEffect(() => {
    if (isOpen) {
      setIssueSummary(initialQuery || "");
      setState("READY");
      setResponse(null);
      setErrorMessage(null);
      setCodeCopied(false);
    }
  }, [isOpen, initialQuery]);

  // Keyboard accessibility: Escape key closes modal (only when not submitting)
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape" && state !== "SUBMITTING") {
        onClose();
      }
    },
    [onClose, state]
  );

  useEffect(() => {
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  const handleCopyReference = () => {
    if (response?.reference_code) {
      navigator.clipboard?.writeText(response.reference_code);
      setCodeCopied(true);
      setTimeout(() => setCodeCopied(false), 2500);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (state === "SUBMITTING") return; // Prevent duplicate submission

    setState("SUBMITTING");
    setErrorMessage(null);

    const descriptionText =
      issueSummary.trim() ||
      initialQuery.trim() ||
      initialGuidance.trim() ||
      "Citizen assistance requested for cooperative inquiry.";

    try {
      const citationsList = initialCitations.map((s) => s.title || String(s));

      const res = await submitHumanHandoff({
        conversation_id: conversationId,
        language: language,
        target_officer_language: officerLanguage,
        citizen_name: citizenName.trim() || null,
        citizen_phone: citizenPhone.trim() || null,
        pacs_name: pacsName.trim() || null,
        village: village.trim() || null,
        category: category,
        description: descriptionText.slice(0, 3900),
        ai_guidance: initialGuidance ? initialGuidance.slice(0, 3900) : null,
        source_citations: citationsList.length > 0 ? citationsList : null,
        priority: "high",
      });

      setResponse(res);
      setState("SUCCESS");
    } catch (err: any) {
      console.error("[HANDOFF_MODAL] Submission error:", err);
      setErrorMessage(err.message || t("handoff.errorMessage"));
      setState("ERROR");
    }
  };

  return (
    <div
      className="modal-backdrop"
      onClick={() => {
        if (state !== "SUBMITTING") onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="handoff-modal-title"
    >
      <div
        className="modal-panel handoff-modal-panel"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header">
          <div className="modal-header-title">
            <LandmarkIcon size={22} color="#123B5D" />
            <h3 id="handoff-modal-title">{t("handoff.modalTitle")}</h3>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            disabled={state === "SUBMITTING"}
            aria-label={t("common.close")}
          >
            <XIcon size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body handoff-modal-body">
          {/* ── STATE: READY or SUBMITTING ── */}
          {(state === "READY" || state === "SUBMITTING") && (
            <form onSubmit={handleSubmit} className="handoff-form">
              {/* Facilitation Explanation Banner */}
              <div className="handoff-explanation-banner">
                <InfoIcon size={18} color="#0F6B68" />
                <div className="handoff-explanation-text">
                  <p className="handoff-explanation-main">
                    {t("handoff.modalExplanation")}
                  </p>
                  <p className="handoff-explanation-sub">
                    {t("handoff.disclaimerNotice")}
                  </p>
                </div>
              </div>

              {/* Pre-filled Context Preview Box */}
              <div className="handoff-context-card">
                <div className="handoff-context-header">
                  <FileTextIcon size={16} color="#123B5D" />
                  <span className="handoff-context-title">
                    {t("handoff.querySummary")}
                  </span>
                </div>
                <div className="handoff-context-body">
                  <textarea
                    className="handoff-textarea"
                    rows={2}
                    value={issueSummary}
                    onChange={(e) => setIssueSummary(e.target.value)}
                    placeholder={initialQuery || "Summary of issue..."}
                    disabled={state === "SUBMITTING"}
                    aria-label={t("handoff.querySummary")}
                  />
                </div>

                {initialCitations && initialCitations.length > 0 && (
                  <div className="handoff-sources-row">
                    <span className="handoff-sources-label">
                      {t("handoff.sourcesLabel")}:
                    </span>
                    <div className="handoff-sources-badges">
                      {initialCitations.slice(0, 3).map((s, idx) => (
                        <span key={idx} className="handoff-source-tag">
                          {s.title}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Optional Citizen & PACS Inputs */}
              <div className="handoff-inputs-grid">
                <div className="handoff-form-group">
                  <label htmlFor="handoff-citizen-name">
                    {t("handoff.citizenName")}
                  </label>
                  <input
                    id="handoff-citizen-name"
                    type="text"
                    className="handoff-input"
                    value={citizenName}
                    onChange={(e) => setCitizenName(e.target.value)}
                    placeholder={t("handoff.citizenNamePlaceholder")}
                    disabled={state === "SUBMITTING"}
                    maxLength={150}
                  />
                </div>

                <div className="handoff-form-group">
                  <label htmlFor="handoff-citizen-phone">
                    {t("handoff.citizenPhone")}
                  </label>
                  <input
                    id="handoff-citizen-phone"
                    type="tel"
                    className="handoff-input"
                    value={citizenPhone}
                    onChange={(e) => setCitizenPhone(e.target.value)}
                    placeholder={t("handoff.citizenPhonePlaceholder")}
                    disabled={state === "SUBMITTING"}
                    maxLength={20}
                  />
                </div>

                <div className="handoff-form-group">
                  <label htmlFor="handoff-pacs-name">
                    {t("handoff.pacsName")}
                  </label>
                  <input
                    id="handoff-pacs-name"
                    type="text"
                    className="handoff-input"
                    value={pacsName}
                    onChange={(e) => setPacsName(e.target.value)}
                    placeholder={t("handoff.pacsNamePlaceholder")}
                    disabled={state === "SUBMITTING"}
                    maxLength={200}
                  />
                </div>

                <div className="handoff-form-group">
                  <label htmlFor="handoff-village">
                    {t("handoff.village")}
                  </label>
                  <input
                    id="handoff-village"
                    type="text"
                    className="handoff-input"
                    value={village}
                    onChange={(e) => setVillage(e.target.value)}
                    placeholder={t("handoff.villagePlaceholder")}
                    disabled={state === "SUBMITTING"}
                    maxLength={150}
                  />
                </div>

                <div className="handoff-form-group handoff-form-group--full">
                  <label htmlFor="handoff-officer-lang">
                    {t("handoff.officerLanguage")}
                  </label>
                  <select
                    id="handoff-officer-lang"
                    className="handoff-select"
                    value={officerLanguage}
                    onChange={(e) => setOfficerLanguage(e.target.value)}
                    disabled={state === "SUBMITTING"}
                  >
                    <option value="en">English (Official Records)</option>
                    <option value="mr">मराठी (Marathi)</option>
                    <option value="hi">हिंदी (Hindi)</option>
                  </select>
                  <span className="handoff-input-help">
                    {t("handoff.translationNotice")}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="modal-footer handoff-modal-footer">
                <button
                  type="button"
                  className="action-btn-secondary"
                  onClick={onClose}
                  disabled={state === "SUBMITTING"}
                >
                  {t("common.cancel")}
                </button>
                <button
                  type="submit"
                  className="action-btn-primary handoff-submit-btn"
                  disabled={state === "SUBMITTING"}
                >
                  {state === "SUBMITTING" ? (
                    <>
                      <span className="handoff-spinner" aria-hidden="true" />
                      <span>{t("handoff.submittingBtn")}</span>
                    </>
                  ) : (
                    <>
                      <LandmarkIcon size={16} color="#FFFFFF" />
                      <span>{t("handoff.submitBtn")}</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* ── STATE: SUCCESS ── */}
          {state === "SUCCESS" && response && (
            <div className="handoff-success-view">
              <div className="handoff-success-icon-badge">
                <CheckCircleIcon size={48} color="#10B981" />
              </div>

              <h4 className="handoff-success-title">
                {t("handoff.successTitle")}
              </h4>

              <div className="handoff-ref-card">
                <div className="handoff-ref-label">
                  {t("handoff.referenceCode")}
                </div>
                <div className="handoff-ref-code-row">
                  <span className="handoff-ref-code">
                    {response.reference_code}
                  </span>
                  <button
                    type="button"
                    className="handoff-copy-code-btn"
                    onClick={handleCopyReference}
                    aria-label="Copy reference code"
                  >
                    {codeCopied ? (
                      <>
                        <CheckIcon size={16} color="#10B981" />
                        <span>{t("common.copied")}</span>
                      </>
                    ) : (
                      <>
                        <CopyIcon size={16} />
                        <span>{t("common.copy")}</span>
                      </>
                    )}
                  </button>
                </div>
                <div className="handoff-privacy-meta">
                  <span>
                    👤 {response.citizen_masked_name} • 📞{" "}
                    {response.citizen_phone_masked}
                  </span>
                  {response.pacs_name && (
                    <span className="handoff-pacs-tag">
                      🏛️ {response.pacs_name}
                    </span>
                  )}
                </div>
              </div>

              <p className="handoff-success-msg">
                {t("handoff.successMessage")}
              </p>

              {/* Translation note */}
              {response.translated_summary && (
                <div className="handoff-translation-preview">
                  <span className="handoff-translation-badge">
                    🌐 Bhashini NMT ({response.citizen_language} →{" "}
                    {response.officer_language})
                  </span>
                  <p className="handoff-translation-text">
                    "{response.translated_summary}"
                  </p>
                </div>
              )}

              {/* Phase 3A.3 Placeholder */}
              <div className="handoff-slip-placeholder">
                <div className="slip-placeholder-header">
                  <ShieldCheckIcon size={18} color="#0F6B68" />
                  <span className="slip-placeholder-title">
                    {t("handoff.slipPlaceholder")}
                  </span>
                </div>
                <p className="slip-placeholder-text">
                  {t("handoff.slipPlaceholderNotice")}
                </p>
              </div>

              <div className="handoff-statutory-disclaimer">
                {response.disclaimer}
              </div>

              <div className="modal-footer handoff-modal-footer">
                <button
                  type="button"
                  className="action-btn-primary"
                  onClick={onClose}
                >
                  {t("handoff.close")}
                </button>
              </div>
            </div>
          )}

          {/* ── STATE: ERROR ── */}
          {state === "ERROR" && (
            <div className="handoff-error-view">
              <div className="handoff-error-icon-badge">
                <AlertTriangleIcon size={48} color="#EF4444" />
              </div>

              <h4 className="handoff-error-title">{t("handoff.errorTitle")}</h4>

              <p className="handoff-error-msg">
                {errorMessage || t("handoff.errorMessage")}
              </p>

              <div className="modal-footer handoff-modal-footer">
                <button
                  type="button"
                  className="action-btn-secondary"
                  onClick={onClose}
                >
                  {t("common.cancel")}
                </button>
                <button
                  type="button"
                  className="action-btn-primary"
                  onClick={() => setState("READY")}
                >
                  {t("handoff.retryBtn")}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HandoffModal;
