import React from "react";
import { ArrowRightIcon, ChevronRightIcon } from "../Icons";

export interface FollowUpAction {
  label: string;
  query: string;
}

interface Props {
  actions: FollowUpAction[];
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
      ? "आप यह भी पूछ सकते हैं"
      : language === "en"
      ? "You may also ask"
      : "तुम्ही हे देखील विचारू शकता";

  return (
    <div className="guidance-next-steps" role="region" aria-label={headerTitle}>
      <div className="guidance-next-steps__header">
        <ArrowRightIcon size={14} color="#0F6B68" />
        <span className="guidance-next-steps__title">{headerTitle}</span>
      </div>
      <div className="guidance-next-steps__list" role="group">
        {actions.map((act, i) => (
          <button
            key={i}
            type="button"
            className="next-step-action-btn"
            onClick={() => onExecuteAction && onExecuteAction(act.query)}
            aria-label={`${act.label} - Click to ask this question`}
          >
            <span className="action-bullet" aria-hidden="true">→</span>
            <span className="action-text">{act.label}</span>
            <ChevronRightIcon size={14} aria-hidden="true" />
          </button>
        ))}
      </div>
    </div>
  );
};

export default NextStepCard;
