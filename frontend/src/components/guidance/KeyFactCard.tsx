import React from "react";
import type { KeyFact } from "../../utils/guidanceParser";
import { InfoIcon } from "../Icons";

interface Props {
  facts: KeyFact[];
  language?: string;
  answerFocus?: string;
}

export const KeyFactCard: React.FC<Props> = ({ facts, language = "mr", answerFocus }) => {
  if (!facts || facts.length === 0) return null;

  const focus = (answerFocus || "OVERVIEW").toUpperCase();

  let headerTitle = "";
  if (focus === "CONTACT") {
    headerTitle =
      language === "hi"
        ? "आधिकारिक संपर्क विवरण एवं हेल्पलाइन"
        : language === "en"
        ? "Official Contact Details & Helpline"
        : "अधिकृत संपर्क व हेल्पलाईन";
  } else if (focus === "DOCUMENTS") {
    headerTitle =
      language === "hi"
        ? "आवश्यक दस्तावेज विवरण"
        : language === "en"
        ? "Required Document Details"
        : "आवश्यक कागदपत्रे तपशील";
  } else if (focus === "PROCEDURE") {
    headerTitle =
      language === "hi"
        ? "मुख्य प्रक्रिया विवरण"
        : language === "en"
        ? "Key Procedural Highlights"
        : "मुख्य प्रक्रिया तपशील";
  } else {
    headerTitle =
      language === "hi"
        ? "मुख्य विवरण"
        : language === "en"
        ? "Key Information & Highlights"
        : "महत्त्वाचे तपशील";
  }

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
