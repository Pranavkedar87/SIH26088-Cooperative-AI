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
  answerFocus?: string;
  onExecuteAction?: (query: string) => void;
  sources?: Array<{ title: string; authority?: string; url?: string }>;
}

export const GuidanceRenderer: React.FC<Props> = ({
  rawContent,
  userQuestion,
  language = "mr",
  answerFocus,
  onExecuteAction,
  sources: _sources,
}) => {
  const guidance: StructuredGuidance = parseGuidance(rawContent, language, answerFocus);

  const focus = (guidance.answerFocus || answerFocus || "OVERVIEW").toUpperCase();

  const isProcedure = focus === "PROCEDURE" || focus === "STEP_BY_STEP";
  const isDocuments = focus === "DOCUMENTS";

  const isProcedureOrDetailRequested = React.useMemo(() => {
    if (!userQuestion) return false;
    const q = userQuestion.toLowerCase();
    return (
      q.includes("procedure") ||
      q.includes("step") ||
      q.includes("detailed") ||
      q.includes("प्रक्रिया") ||
      q.includes("टप्पा") ||
      q.includes("सविस्तर")
    );
  }, [userQuestion]);

  const [showExtraDetails, setShowExtraDetails] = useState<boolean>(isProcedureOrDetailRequested);

  // Focus-Driven Section Visibility Rules:
  // 1. StepTimeline renders ONLY for PROCEDURE focus
  const renderSteps = isProcedure && guidance.steps.length > 0;

  // 2. Checklist renders for DOCUMENTS or PROCEDURE focus
  const renderChecklist = (isDocuments || isProcedure) && guidance.checklist.length > 0;

  // 3. KeyFacts renders when present
  const renderFacts = guidance.keyFacts.length > 0;

  // 4. Warnings render when present
  const renderWarnings = guidance.warnings.length > 0;

  // 5. Paragraphs render when present
  const renderParagraphs = guidance.cleanParagraphs.length > 0;

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
      {renderWarnings && <WarningCard warnings={guidance.warnings} language={language} />}

      {/* 3. Compact Key Facts / Contact Grid */}
      {renderFacts && <KeyFactCard facts={guidance.keyFacts} language={language} answerFocus={focus} />}

      {/* 4. Step-by-Step Procedure Timeline (Rendered ONLY when focus = PROCEDURE) */}
      {renderSteps && <StepTimeline steps={guidance.steps} language={language} />}

      {/* 5. Requirements Checklist (Rendered for DOCUMENTS or PROCEDURE focus) */}
      {renderChecklist && <Checklist items={guidance.checklist} language={language} />}

      {/* 6. Core Action Card: "पुढे काय करावे?" (Non-redundant follow-up buttons) */}
      <NextStepCard
        actions={guidance.nextActions}
        onExecuteAction={onExecuteAction}
        language={language}
      />

      {/* 7. Optional Expandable Detailed Information */}
      {renderParagraphs && (
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
