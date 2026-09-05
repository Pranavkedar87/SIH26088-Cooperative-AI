import React from "react";
import type { AnswerSection } from "../utils/parseAnswer";
import { bodyToLines } from "../utils/parseAnswer";

interface Props {
  sections: AnswerSection[];
}

const SECTION_META: Record<string, { icon: string; label: string; className: string }> = {
  DIRECT_ANSWER: { icon: "✅", label: "Direct Answer", className: "sa-section--direct" },
  WHAT_YOU_CAN_DO: { icon: "📋", label: "What You Can Do", className: "sa-section--actions" },
  IMPORTANT: { icon: "⚠️", label: "Important", className: "sa-section--important" },
  NEXT_STEP: { icon: "➡️", label: "Next Step", className: "sa-section--next" },
  PLAIN: { icon: "", label: "", className: "sa-section--plain" },
};

const StructuredAnswer: React.FC<Props> = ({ sections }) => {
  if (!sections || sections.length === 0) return null;

  return (
    <div className="structured-answer">
      {sections.map((section, idx) => {
        const meta = SECTION_META[section.kind] ?? SECTION_META.PLAIN;
        const lines = bodyToLines(section.body);
        const isList = lines.some((l) => l.startsWith("-") || l.startsWith("•") || l.startsWith("*"));

        return (
          <div key={idx} className={`sa-section ${meta.className}`}>
            {section.kind !== "PLAIN" && (
              <div className="sa-section__header">
                {meta.icon && <span className="sa-section__icon" aria-hidden="true">{meta.icon}</span>}
                <span className="sa-section__label">{section.heading || meta.label}</span>
              </div>
            )}
            <div className="sa-section__body">
              {isList ? (
                <ul className="sa-list">
                  {lines
                    .map((l) => l.replace(/^[-•*]\s*/, "").trim())
                    .filter(Boolean)
                    .map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                </ul>
              ) : (
                lines.map((line, i) => (
                  <p key={i}>{line}</p>
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StructuredAnswer;
