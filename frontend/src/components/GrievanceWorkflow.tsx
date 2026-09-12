import React, { useState } from "react";
import type { LanguageCode } from "../types";
import { useTranslation } from "../i18n";
import {
  ClipboardCheckIcon,
  CopyIcon,
  ShieldCheckIcon,
  ArrowRightIcon,
} from "./Icons";

interface Props {
  language: LanguageCode;
  onSaveHistory?: (title: string, subtitle: string, details: string) => void;
}

interface IssueCategory {
  id: string;
  en: string;
  hi: string;
  mr: string;
}

const CATEGORIES: IssueCategory[] = [
  { id: "membership", en: "Membership Denial / Disqualification", hi: "सदस्यता से इनकार / अयोग्यता", mr: "सभासदत्व नाकारणे / अपात्रता" },
  { id: "loan", en: "Crop Loan / Interest Subvention Issue", hi: "फसल ऋण / ब्याज छूट समस्या", mr: "पीक कर्ज / व्याज सवलत समस्या" },
  { id: "pmfby_claim", en: "PMFBY Claim Delay / Rejection", hi: "फसल बीमा दावा में देरी / अस्वीकृति", mr: "पीक विमा दावा उशीर / फेटाळणे" },
  { id: "election", en: "Managing Committee / Election Dispute", hi: "प्रबंध समिति / चुनाव विवाद", mr: "संचालक मंडळ / निवडणूक विवाद" },
  { id: "pacs_service", en: "PACS Fertilizer / Warehouse Denial", hi: "पैक्स खाद / भंडारण से इनकार", mr: "PACS खते / गोदाम नाकारणे" },
  { id: "governance", en: "Financial Irregularity / Audit Failure", hi: "वित्तीय अनियमितता / ऑडिट विफलता", mr: "आर्थिक गैरव्यवहार / ऑडिट त्रुटी" },
];

const GrievanceWorkflow: React.FC<Props> = ({ language, onSaveHistory }) => {
  const t = useTranslation(language);
  const [step, setStep] = useState<number>(1);
  const [category, setCategory] = useState<IssueCategory>(CATEGORIES[0]);
  const [societyName, setSocietyName] = useState<string>("");
  const [district, setDistrict] = useState<string>("");
  const [details, setDetails] = useState<string>("");
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopySummary = (summaryText: string) => {
    navigator.clipboard?.writeText(summaryText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleDownloadSummary = (summaryText: string) => {
    const element = document.createElement("a");
    const file = new Blob([summaryText], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = `Grievance_Summary_${Date.now()}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const categoryName = (category as any)[language] ?? category.en;

  const generatedSummary = `=== FORMAL COOPERATIVE GRIEVANCE SUMMARY ===
Date: ${new Date().toLocaleDateString()}
Category: ${category.en} (${categoryName})
Cooperative Society / PACS: ${societyName || "Not specified"}
District / Location: ${district || "Not specified"}

SUMMARY OF PROBLEM & INCIDENT:
${details || "No specific details entered."}

RECOMMENDED OFFICIAL ACTION STEPS:
1. Submit this formal written complaint to the Chairman/Secretary of ${societyName || "the society"} via registered post or in-person receipt.
2. If unresolved within 15 days, forward this complaint summary along with your acknowledgment receipt to the District Deputy Registrar (DDR) of Cooperative Societies.
3. For PMFBY claims, submit a copy to the District Agriculture Officer (DAO) and Insurance Company Grievance Nodal Officer.

LEGAL DISCLAIMER:
SahkaarSetu provides structured guidance and summary compilation based on official Maharashtra Cooperative rules. SahkaarSetu does not file official legal claims directly with court/government authorities.`;

  const handleComplete = () => {
    if (onSaveHistory) {
      onSaveHistory(
        `Grievance: ${categoryName}`,
        `Society: ${societyName || "General"}, District: ${district || "Local"}`,
        generatedSummary
      );
    }
  };

  return (
    <div className="grievance-workflow" aria-label="Grievance Assistance Wizard">
      {/* Header Bar */}
      <div className="grievance-header">
        <div className="grievance-header__icon">
          <ClipboardCheckIcon size={24} color="#176B5B" />
        </div>
        <div className="grievance-header__text">
          <h3 className="grievance-title">{t("grievance.title")}</h3>
          <p className="grievance-sub">{t("grievance.subtitle")}</p>
        </div>
      </div>

      {/* Progress Node Line */}
      <div className="grievance-progress">
        <div className={`grievance-step-node ${step >= 1 ? "grievance-step-node--active" : ""}`}>
          <span>1. {t("grievance.step1Label")}</span>
        </div>
        <div className="grievance-progress-line" />
        <div className={`grievance-step-node ${step >= 2 ? "grievance-step-node--active" : ""}`}>
          <span>2. {t("grievance.step2Label")}</span>
        </div>
        <div className="grievance-progress-line" />
        <div className={`grievance-step-node ${step >= 3 ? "grievance-step-node--active" : ""}`}>
          <span>3. {t("grievance.step3Label")}</span>
        </div>
      </div>

      {/* Panels */}
      <div className="grievance-body">
        {step === 1 && (
          <div className="grievance-panel">
            <h4 className="grievance-panel-heading">
              {t("grievance.step1Heading")}
            </h4>
            <div className="grievance-cat-list">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  className={`grievance-cat-btn ${category.id === cat.id ? "grievance-cat-btn--selected" : ""}`}
                  onClick={() => setCategory(cat)}
                >
                  <span className="cat-radio">{category.id === cat.id ? "●" : "○"}</span>
                  <span className="cat-label">{(cat as any)[language] ?? cat.en}</span>
                </button>
              ))}
            </div>
            <button
              type="button"
              className="grievance-main-btn"
              onClick={() => setStep(2)}
            >
              <span>{t("grievance.enterDetails")}</span>
              <ArrowRightIcon size={16} color="#FFFFFF" />
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="grievance-panel">
            <h4 className="grievance-panel-heading">
              {t("grievance.step2Heading")}
            </h4>

            <div className="form-group">
              <label className="form-label">
                {t("grievance.societyName")}
              </label>
              <input
                type="text"
                className="form-input"
                value={societyName}
                onChange={(e) => setSocietyName(e.target.value)}
                placeholder={t("grievance.societyPlaceholder")}
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                {t("grievance.district")}
              </label>
              <input
                type="text"
                className="form-input"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                placeholder={t("grievance.districtPlaceholder")}
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                {t("grievance.issueDescription")}
              </label>
              <textarea
                className="form-textarea"
                rows={4}
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                placeholder={t("grievance.issuePlaceholder")}
              />
            </div>

            <div className="grievance-btn-row">
              <button type="button" className="grievance-sec-btn" onClick={() => setStep(1)}>
                ← {t("common.back")}
              </button>
              <button
                type="button"
                className="grievance-main-btn"
                onClick={() => {
                  setStep(3);
                  handleComplete();
                }}
              >
                <span>{t("grievance.generateSummary")}</span>
                <ArrowRightIcon size={16} color="#FFFFFF" />
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="grievance-panel">
            <h4 className="grievance-panel-heading">
              {t("grievance.step3Heading")}
            </h4>

            <pre className="summary-preview">{generatedSummary}</pre>

            <div className="disclaimer-callout">
              <ShieldCheckIcon size={16} color="#F28C28" />
              <span>
                {t("grievance.disclaimer")}
              </span>
            </div>

            <div className="grievance-btn-row">
              <button
                type="button"
                className="grievance-sec-btn"
                onClick={() => handleCopySummary(generatedSummary)}
              >
                <CopyIcon size={14} color="#24323A" />
                <span>{copied ? t("common.copied") : t("grievance.copy")}</span>
              </button>
              <button
                type="button"
                className="grievance-main-btn"
                onClick={() => handleDownloadSummary(generatedSummary)}
              >
                <span>{t("grievance.download")}</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GrievanceWorkflow;
