import React from "react";
import type { AnswerSection } from "../utils/parseAnswer";
import { bodyToLines } from "../utils/parseAnswer";

interface Props {
  sections: AnswerSection[];
}

const SECTION_TITLE_MAP: Record<string, { label: string; className: string }> = {
  DIRECT_ANSWER: { label: "UNDERSTAND", className: "sa-block--understand" },
  WHAT_YOU_CAN_DO: { label: "NEXT STEPS", className: "sa-block--next-steps" },
  IMPORTANT: { label: "YOU MAY NEED", className: "sa-block--need" },
  NEXT_STEP: { label: "ACTION PLAN", className: "sa-block--action" },
  PLAIN: { label: "", className: "sa-block--plain" },
};

const StructuredAnswer: React.FC<Props> = ({ sections }) => {
  if (!sections || sections.length === 0) return null;

  return (
    <div className="structured-answer-block">
      {sections.map((section, idx) => {
        const meta = SECTION_TITLE_MAP[section.kind] ?? SECTION_TITLE_MAP.PLAIN;
        const lines = bodyToLines(section.body);
        const isList = lines.some(
          (l) => l.startsWith("-") || l.startsWith("•") || l.startsWith("*") || /^\d+\./.test(l)
        );

        return (
          <div key={idx} className={`sa-block ${meta.className}`}>
            {section.kind !== "PLAIN" && (
              <div className="sa-block__header">
                <span className="sa-block__title">{section.heading || meta.label}</span>
              </div>
            )}
            <div className="sa-block__body">
              {isList ? (
                <ol className="sa-numbered-list">
                  {lines
                    .map((l) => l.replace(/^([-•*]|\d+\.)\s*/, "").trim())
                    .filter(Boolean)
                    .map((item, i) => (
                      <li key={i}>
                        <span className="num-badge">{String(i + 1).padStart(2, "0")}</span>
                        <span className="list-text">{item}</span>
                      </li>
                    ))}
                </ol>
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
