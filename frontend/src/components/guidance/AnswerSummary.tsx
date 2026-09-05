import React from "react";
import { ShieldCheckIcon } from "../Icons";

interface Props {
  summary: string;
  domainLabel: string;
  language?: string;
}

export const AnswerSummary: React.FC<Props> = ({ summary, domainLabel }) => {
  if (!summary) return null;

  return (
    <div className="guidance-summary">
      <div className="guidance-summary__header">
        <div className="guidance-summary__tag">
          <ShieldCheckIcon size={14} color="#176B5B" />
          <span>{domainLabel}</span>
        </div>
      </div>
      <p className="guidance-summary__text">{summary}</p>
    </div>
  );
};

export default AnswerSummary;
