import React, { useState } from "react";
import type { LanguageCode } from "../types";
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

  const categoryName = category[language] ?? category.en;

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
          <h3 className="grievance-title">
            {language === "hi" ? "सहकारी शिकायत सहायता" : language === "mr" ? "सहकारी तक्रार निवारण मार्गदर्शक" : "Grievance Assistance"}
          </h3>
          <p className="grievance-sub">
            {language === "hi"
              ? "आधिकारिक प्रस्तुति के लिए संरचित शिकायत सारांश तैयार करें"
              : language === "mr"
              ? "अधिकृत सादरकरणासाठी रचनात्मक तक्रार सारांश तयार करा"
              : "Tell us what happened to compile a formal complaint summary for District Deputy Registrar (DDR) submission"}
          </p>
        </div>
      </div>

      {/* Progress Node Line */}
      <div className="grievance-progress">
        <div className={`grievance-step-node ${step >= 1 ? "grievance-step-node--active" : ""}`}>
          <span>1. Select Issue</span>
        </div>
        <div className="grievance-progress-line" />
        <div className={`grievance-step-node ${step >= 2 ? "grievance-step-node--active" : ""}`}>
          <span>2. Enter Details</span>
        </div>
        <div className="grievance-progress-line" />
        <div className={`grievance-step-node ${step >= 3 ? "grievance-step-node--active" : ""}`}>
          <span>3. Formal Summary</span>
        </div>
      </div>

      {/* Panels */}
      <div className="grievance-body">
        {step === 1 && (
          <div className="grievance-panel">
            <h4 className="grievance-panel-heading">
              {language === "hi" ? "अपनी शिकायत श्रेणी चुनें" : language === "mr" ? "तुमच्या तक्रारीचा प्रकार निवडा" : "Step 1: Select your complaint category"}
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
                  <span className="cat-label">{cat[language] ?? cat.en}</span>
                </button>
              ))}
            </div>
            <button
              type="button"
              className="grievance-main-btn"
              onClick={() => setStep(2)}
            >
              <span>{language === "hi" ? "विवरण दर्ज करें" : language === "mr" ? "तपशील नोंदवा" : "Enter Details"}</span>
              <ArrowRightIcon size={16} color="#FFFFFF" />
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="grievance-panel">
            <h4 className="grievance-panel-heading">
              {language === "hi" ? "समिति एवं घटना का विवरण दें" : language === "mr" ? "संस्था व समस्येचे वर्णन करा" : "Step 2: Describe the problem & society details"}
            </h4>

            <div className="form-group">
              <label className="form-label">
                {language === "hi" ? "सहकारी समिति का नाम:" : language === "mr" ? "सहकारी संस्थेचे नाव:" : "Name of Cooperative Society / PACS:"}
              </label>
              <input
                type="text"
                className="form-input"
                value={societyName}
                onChange={(e) => setSocietyName(e.target.value)}
                placeholder="e.g. Vividh Karyakari Seva Sahakari Sanstha Maryadit"
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                {language === "hi" ? "जिला / तालुका:" : language === "mr" ? "जिल्हा / तालुका:" : "District / Taluka:"}
              </label>
              <input
                type="text"
                className="form-input"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                placeholder="e.g. Chhatrapati Sambhajinagar"
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                {language === "hi" ? "समस्या का विवरण दर्ज करें:" : language === "mr" ? "समस्येचे सविस्तर वर्णन करा:" : "Description of problem / incident:"}
              </label>
              <textarea
                className="form-textarea"
                rows={4}
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                placeholder="Describe what happened, dates, loan account numbers, or refusal details…"
              />
            </div>

            <div className="grievance-btn-row">
              <button type="button" className="grievance-sec-btn" onClick={() => setStep(1)}>
                ← {language === "hi" ? "पिछला" : language === "mr" ? "मागे" : "Previous"}
              </button>
              <button
                type="button"
                className="grievance-main-btn"
                onClick={() => {
                  setStep(3);
                  handleComplete();
                }}
              >
                <span>{language === "hi" ? "सारांश बनाएं" : language === "mr" ? "सारांश तयार करा" : "Generate Summary"}</span>
                <ArrowRightIcon size={16} color="#FFFFFF" />
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="grievance-panel">
            <h4 className="grievance-panel-heading">
              {language === "hi" ? "आपकी संरचित शिकायत सारांश" : language === "mr" ? "तुमचा रचनात्मक तक्रार सारांश" : "YOUR GRIEVANCE SUMMARY"}
            </h4>

            <pre className="summary-preview">{generatedSummary}</pre>

            <div className="disclaimer-callout">
              <ShieldCheckIcon size={16} color="#B7791F" />
              <span>
                <strong>Notice:</strong> SahkaarSetu provides structured complaint guidance based on official Maharashtra Cooperative rules. SahkaarSetu does not file official legal claims directly with court/government authorities.
              </span>
            </div>

            <div className="grievance-btn-row">
              <button
                type="button"
                className="grievance-sec-btn"
                onClick={() => handleCopySummary(generatedSummary)}
              >
                <CopyIcon size={14} color="#17363A" />
                <span>{copied ? "✓ Copied!" : "Copy Summary"}</span>
              </button>
              <button
                type="button"
                className="grievance-main-btn"
                onClick={() => handleDownloadSummary(generatedSummary)}
              >
                <span>Download (.txt)</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GrievanceWorkflow;
