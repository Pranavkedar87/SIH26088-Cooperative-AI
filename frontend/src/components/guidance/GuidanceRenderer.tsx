import React, { useState } from "react";
import { parseGuidance, type StructuredGuidance } from "../../utils/guidanceParser";
import AnswerSummary from "./AnswerSummary";
import KeyFactCard from "./KeyFactCard";
import StepTimeline from "./StepTimeline";
import Checklist from "./Checklist";
import WarningCard from "./WarningCard";
import NextStepCard from "./NextStepCard";

interface Props {
  rawContent: string;
  language?: string;
  onFollowUp?: (prompt: string) => void;
}

export type ViewMode = "QUICK" | "GUIDED" | "DETAILED";

export const GuidanceRenderer: React.FC<Props> = ({
  rawContent,
  language = "mr",
  onFollowUp,
}) => {
  const guidance: StructuredGuidance = parseGuidance(rawContent, language);
  const [viewMode, setViewMode] = useState<ViewMode>("GUIDED");

  const hasFacts = guidance.keyFacts.length > 0;
  const hasSteps = guidance.steps.length > 0;
  const hasChecklist = guidance.checklist.length > 0;
  const hasWarnings = guidance.warnings.length > 0;

  return (
    <div className="guidance-system">
      {/* Response View Mode Switcher (Progressive Disclosure) */}
      <div className="guidance-toolbar">
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

      {/* 1. Summary Section (Always shown first) */}
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

          {/* Clean Paragraphs */}
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
        nextSteps={guidance.nextSteps}
        domain={guidance.domain}
        onFollowUp={onFollowUp}
        language={language}
      />
    </div>
  );
};

export default GuidanceRenderer;
