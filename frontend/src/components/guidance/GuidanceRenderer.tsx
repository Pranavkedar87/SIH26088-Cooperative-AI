import React, { useState } from "react";
import { parseGuidance, type StructuredGuidance } from "../../utils/guidanceParser";
import { generateGuidancePdf } from "../../utils/pdfGenerator";
import AnswerSummary from "./AnswerSummary";
import KeyFactCard from "./KeyFactCard";
import StepTimeline from "./StepTimeline";
import Checklist from "./Checklist";
import WarningCard from "./WarningCard";
import NextStepCard from "./NextStepCard";
import { FileTextIcon } from "../Icons";

interface Props {
  rawContent: string;
  userQuestion?: string;
  language?: string;
  onExecuteAction?: (query: string) => void;
  sources?: Array<{ title: string; authority?: string; url?: string }>;
}

export type ViewMode = "QUICK" | "GUIDED" | "DETAILED";

export const GuidanceRenderer: React.FC<Props> = ({
  rawContent,
  userQuestion,
  language = "mr",
  onExecuteAction,
  sources,
}) => {
  const guidance: StructuredGuidance = parseGuidance(rawContent, language);
  const [viewMode, setViewMode] = useState<ViewMode>("GUIDED");
  const [isGeneratingPdf, setIsGeneratingPdf] = useState<boolean>(false);

  const hasFacts = guidance.keyFacts.length > 0;
  const hasSteps = guidance.steps.length > 0;
  const hasChecklist = guidance.checklist.length > 0;
  const hasWarnings = guidance.warnings.length > 0;

  const handleDownloadPdf = async () => {
    try {
      setIsGeneratingPdf(true);
      await generateGuidancePdf({
        question: userQuestion,
        language,
        domainLabel: guidance.domainLabel,
        summary: guidance.summary,
        keyFacts: guidance.keyFacts,
        steps: guidance.steps,
        warnings: guidance.warnings,
        nextSteps: guidance.nextSteps,
        sources: sources?.map((s) => ({ title: s.title, authority: s.authority, url: s.url })),
      });
    } catch (err) {
      console.error("PDF download error:", err);
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  return (
    <div className="guidance-system">
      {/* Response View Mode & Action Toolbar */}
      <div className="guidance-toolbar">
        <button
          type="button"
          className="pdf-download-btn"
          onClick={handleDownloadPdf}
          disabled={isGeneratingPdf}
          title="Download official guidance PDF"
        >
          <FileTextIcon size={14} color="#126B62" />
          <span>
            {isGeneratingPdf
              ? language === "hi"
                ? "पीडीएफ बन रहा है..."
                : language === "en"
                ? "Generating PDF..."
                : "PDF तयार होत आहे..."
              : language === "hi"
              ? "मार्गदर्शन PDF"
              : language === "en"
              ? "Guidance PDF"
              : "मार्गदर्शन PDF"}
          </span>
        </button>

        <div className="guidance-toolbar__modes">
          <button
            type="button"
            className={`mode-pill ${viewMode === "QUICK" ? "is-active" : ""}`}
            onClick={() => setViewMode("QUICK")}
          >
            {language === "hi" ? "संक्षिप्त" : language === "en" ? "Summary" : "थोडक्यात"}
          </button>

          {hasSteps && (
            <button
              type="button"
              className={`mode-pill ${viewMode === "GUIDED" ? "is-active" : ""}`}
              onClick={() => setViewMode("GUIDED")}
            >
              {language === "hi" ? "चरण-दर-चरण" : language === "en" ? "Steps" : "पायऱ्या"}
            </button>
          )}

          <button
            type="button"
            className={`mode-pill ${viewMode === "DETAILED" ? "is-active" : ""}`}
            onClick={() => setViewMode("DETAILED")}
          >
            {language === "hi" ? "विस्तृत" : language === "en" ? "Detailed" : "सविस्तर माहिती"}
          </button>
        </div>
      </div>

      {/* 1. Summary Section (Descriptive Explanation FIRST) */}
      <AnswerSummary
        summary={guidance.summary}
        domainLabel={guidance.domainLabel}
        language={language}
      />

      {/* 2. Warning Callouts */}
      {hasWarnings && <WarningCard warnings={guidance.warnings} language={language} />}

      {/* Mode View: QUICK */}
      {viewMode === "QUICK" && (
        <>
          {hasFacts && <KeyFactCard facts={guidance.keyFacts} language={language} />}
        </>
      )}

      {/* Mode View: GUIDED */}
      {viewMode === "GUIDED" && (
        <>
          {hasFacts && <KeyFactCard facts={guidance.keyFacts} language={language} />}
          {hasSteps && <StepTimeline steps={guidance.steps} language={language} />}
        </>
      )}

      {/* Mode View: DETAILED */}
      {viewMode === "DETAILED" && (
        <>
          {hasFacts && <KeyFactCard facts={guidance.keyFacts} language={language} />}
          {hasSteps && <StepTimeline steps={guidance.steps} language={language} />}
          {hasChecklist && <Checklist items={guidance.checklist} language={language} />}

          {guidance.cleanParagraphs.length > 0 && (
            <div className="guidance-detailed-text">
              {guidance.cleanParagraphs.map((para, i) => (
                <p key={i} className="guidance-para">
                  {para}
                </p>
              ))}
            </div>
          )}
        </>
      )}

      {/* 3. Action Card: "What Should I Do Now?" */}
      <NextStepCard
        actions={guidance.nextActions}
        onExecuteAction={onExecuteAction}
        language={language}
      />
    </div>
  );
};

export default GuidanceRenderer;
