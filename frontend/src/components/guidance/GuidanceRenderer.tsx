import React, { useState } from "react";
import { parseGuidance, type StructuredGuidance } from "../../utils/guidanceParser";
import AnswerSummary from "./AnswerSummary";
import KeyFactCard from "./KeyFactCard";
import StepTimeline from "./StepTimeline";
import Checklist from "./Checklist";
import WarningCard from "./WarningCard";
import NextStepCard from "./NextStepCard";
import { ChevronRightIcon } from "../Icons";

interface Props {
  rawContent: string;
  userQuestion?: string;
  language?: string;
  onExecuteAction?: (query: string) => void;
  sources?: Array<{ title: string; authority?: string; url?: string }>;
}

export const GuidanceRenderer: React.FC<Props> = ({
  rawContent,
  userQuestion,
  language = "mr",
  onExecuteAction,
  sources: _sources,
}) => {
  const guidance: StructuredGuidance = parseGuidance(rawContent, language);
  
  const isProcedureOrDetailRequested = React.useMemo(() => {
    if (!userQuestion) return false;
    const q = userQuestion.toLowerCase();
    return (
      q.includes("procedure") ||
      q.includes("step") ||
      q.includes("detailed") ||
      q.includes("प्रक्रिया") ||
      q.includes("टप्पा") ||
      q.includes("सविस्तर") ||
      q.includes("दस्तावेज")
    );
  }, [userQuestion]);

  const [showExtraDetails, setShowExtraDetails] = useState<boolean>(isProcedureOrDetailRequested);

  const hasFacts = guidance.keyFacts.length > 0;
  const hasSteps = guidance.steps.length > 0;
  const hasChecklist = guidance.checklist.length > 0;
  const hasWarnings = guidance.warnings.length > 0;
  const hasExtraParagraphs = guidance.cleanParagraphs.length > 0;

  const expandBtnLabel =
    language === "hi"
      ? "विस्तृत जानकारी देखें"
      : language === "en"
      ? "View Detailed Information"
      : "विस्तृत माहिती पाहा";

  return (
    <div className="guidance-system">
      {/* 1. Summary Section (Natural Descriptive Explanation FIRST) */}
      <AnswerSummary
        summary={guidance.summary}
        domainLabel={guidance.domainLabel}
        language={language}
      />

      {/* 2. Warning Callouts */}
      {hasWarnings && <WarningCard warnings={guidance.warnings} language={language} />}

      {/* 3. Compact Key Facts Grid (Short metrics only) */}
      {hasFacts && <KeyFactCard facts={guidance.keyFacts} language={language} />}

      {/* 4. Step-by-Step Procedure Timeline */}
      {hasSteps && <StepTimeline steps={guidance.steps} language={language} />}

      {/* 5. Requirements Checklist */}
      {hasChecklist && <Checklist items={guidance.checklist} language={language} />}

      {/* 6. Core Action Card: "पुढे काय करावे?" */}
      <NextStepCard
        actions={guidance.nextActions}
        onExecuteAction={onExecuteAction}
        language={language}
      />

      {/* 7. Optional Expandable Detailed Information (NOT a mode switch toggle) */}
      {hasExtraParagraphs && (
        <div className="guidance-expandable-section">
          <button
            type="button"
            className="expand-details-btn"
            onClick={() => setShowExtraDetails((prev) => !prev)}
          >
            <span>{expandBtnLabel}</span>
            <span className={`chevron-icon ${showExtraDetails ? "rotated" : ""}`}>
              <ChevronRightIcon size={14} />
            </span>
          </button>

          {showExtraDetails && (
            <div className="guidance-detailed-text show-details">
              {guidance.cleanParagraphs.map((para, i) => (
                <p key={i} className="guidance-para">
                  {para}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GuidanceRenderer;
