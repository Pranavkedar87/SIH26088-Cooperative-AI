import React, { useState } from "react";
import type { GuidanceStep } from "../../utils/guidanceParser";
import { ChevronRightIcon, ArrowRightIcon } from "../Icons";

interface Props {
  steps: GuidanceStep[];
  language?: string;
}

export const StepTimeline: React.FC<Props> = ({ steps, language = "mr" }) => {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  if (!steps || steps.length === 0) return null;

  const headerTitle =
    language === "hi"
      ? "प्रक्रिया के चरण"
      : language === "en"
      ? "Step-by-Step Procedure"
      : "नुकसान भरपाई / अर्ज प्रक्रिया";

  const toggleExpand = (stepNum: number) => {
    setExpandedStep((curr) => (curr === stepNum ? null : stepNum));
  };

  return (
    <div className="guidance-timeline-block">
      <div className="guidance-section-label">
        <ArrowRightIcon size={14} color="#176B5B" />
        <span>{headerTitle}</span>
      </div>
      <div className="step-timeline">
        {steps.map((step) => {
          const isExpanded = expandedStep === step.stepNum;
          const hasDesc = !!step.description;

          return (
            <div
              key={step.stepNum}
              className={`step-timeline__item ${isExpanded ? "is-expanded" : ""}`}
              onClick={() => hasDesc && toggleExpand(step.stepNum)}
            >
              <div className="step-timeline__badge">{String(step.stepNum).padStart(2, "0")}</div>
              <div className="step-timeline__content">
                <div className="step-timeline__title-row">
                  <h4 className="step-timeline__title">{step.title}</h4>
                  {hasDesc && (
                    <span className={`step-timeline__chevron ${isExpanded ? "rotated" : ""}`}>
                      <ChevronRightIcon size={14} />
                    </span>
                  )}
                </div>
                {step.description && (
                  <p
                    className={`step-timeline__desc ${
                      isExpanded ? "show-all" : "preview-line"
                    }`}
                  >
                    {step.description}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StepTimeline;
