import React from "react";
import type { AnswerSection } from "../utils/parseAnswer";
import { bodyToLines } from "../utils/parseAnswer";
import { CheckVerifiedIcon } from "./Icons";

interface Props {
  sections: AnswerSection[];
}

const SECTION_META: Record<string, { label: string; className: string }> = {
  DIRECT_ANSWER: { label: "Direct Answer", className: "sa-card--direct" },
  WHAT_YOU_CAN_DO: { label: "What You Can Do", className: "sa-card--actions" },
  IMPORTANT: { label: "Important", className: "sa-card--important" },
  NEXT_STEP: { label: "Next Step", className: "sa-card--next" },
  PLAIN: { label: "", className: "sa-card--plain" },
};

const StructuredAnswer: React.FC<Props> = ({ sections }) => {
  if (!sections || sections.length === 0) return null;

  return (
    <div className="structured-answer-container">
      {sections.map((section, idx) => {
        const meta = SECTION_META[section.kind] ?? SECTION_META.PLAIN;
        const lines = bodyToLines(section.body);
        const isList = lines.some(
          (l) => l.startsWith("-") || l.startsWith("•") || l.startsWith("*") || /^\d+\./.test(l)
        );

        return (
          <div key={idx} className={`sa-card ${meta.className}`}>
            {section.kind !== "PLAIN" && (
              <div className="sa-card__header">
                {section.kind === "DIRECT_ANSWER" && (
                  <CheckVerifiedIcon size={14} color="#2A7B4C" />
                )}
                <span className="sa-card__title">{section.heading || meta.label}</span>
              </div>
            )}
            <div className="sa-card__body">
              {isList ? (
                <ul className="sa-bullet-list">
                  {lines
                    .map((l) => l.replace(/^([-•*]|\d+\.)\s*/, "").trim())
                    .filter(Boolean)
                    .map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                </ul>
              ) : (
                lines.map((line, i) => <p key={i}>{line}</p>)
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StructuredAnswer;
