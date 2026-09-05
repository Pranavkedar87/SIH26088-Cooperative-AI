import React from "react";
import { CheckCircleIcon } from "../Icons";

interface Props {
  items: string[];
  language?: string;
}

export const Checklist: React.FC<Props> = ({ items, language = "mr" }) => {
  if (!items || items.length === 0) return null;

  const headerTitle =
    language === "hi"
      ? "आवश्यक सूची"
      : language === "en"
      ? "Checklist & Requirements"
      : "आवश्यक कागदपत्रे व बाबी";

  return (
    <div className="guidance-checklist-block">
      <div className="guidance-section-label">
        <CheckCircleIcon size={14} color="#176B5B" />
        <span>{headerTitle}</span>
      </div>
      <ul className="guidance-checklist">
        {items.map((item, idx) => (
          <li key={idx} className="guidance-checklist__item">
            <span className="checklist-icon">
              <CheckCircleIcon size={14} color="#176B5B" />
            </span>
            <span className="checklist-text">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Checklist;
