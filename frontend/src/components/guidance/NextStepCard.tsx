import React from "react";
import type { NextAction } from "../../utils/guidanceParser";
import { ArrowRightIcon, ChevronRightIcon } from "../Icons";

interface Props {
  actions: NextAction[];
  onExecuteAction?: (query: string) => void;
  language?: string;
}

export const NextStepCard: React.FC<Props> = ({
  actions,
  onExecuteAction,
  language = "mr",
}) => {
  if (!actions || actions.length === 0) return null;

  const headerTitle =
    language === "hi"
      ? "सुझाए गए प्रश्न"
      : language === "en"
      ? "Suggested Follow-ups"
      : "पुढील पर्याय";

  return (
    <div className="guidance-next-steps">
      <div className="guidance-next-steps__header">
        <ArrowRightIcon size={14} color="#176B5B" />
        <span>{headerTitle}</span>
      </div>
      <div className="guidance-next-steps__list">
        {actions.map((act, i) => (
          <button
            key={i}
            type="button"
            className="next-step-action-btn"
            onClick={() => onExecuteAction && onExecuteAction(act.query)}
          >
            <span className="action-bullet">→</span>
            <span className="action-text">{act.label}</span>
            <ChevronRightIcon size={14} />
          </button>
        ))}
      </div>
    </div>
  );
};

export default NextStepCard;
