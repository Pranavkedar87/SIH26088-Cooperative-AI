import React from "react";
import type { KeyFact } from "../../utils/guidanceParser";
import { InfoIcon } from "../Icons";

interface Props {
  facts: KeyFact[];
  language?: string;
}

export const KeyFactCard: React.FC<Props> = ({ facts, language = "mr" }) => {
  if (!facts || facts.length === 0) return null;

  const headerTitle =
    language === "hi"
      ? "मुख्य विवरण / दरें"
      : language === "en"
      ? "Key Highlights & Rates"
      : "महत्त्वाचे तपशील व दर";

  return (
    <div className="guidance-facts-block">
      <div className="guidance-section-label">
        <InfoIcon size={14} color="#104F55" />
        <span>{headerTitle}</span>
      </div>
      <div className="guidance-facts-grid">
        {facts.map((fact, i) => (
          <div
            key={i}
            className={`fact-card ${fact.highlight ? "fact-card--highlight" : ""}`}
          >
            <div className="fact-card__label">{fact.label}</div>
            <div className="fact-card__value">{fact.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default KeyFactCard;
