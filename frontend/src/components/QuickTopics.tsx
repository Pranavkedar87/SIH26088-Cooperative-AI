import React from "react";
import type { LanguageCode, QuickTopic } from "../types";
import { QUICK_TOPICS } from "../types";

interface Props {
  language: LanguageCode;
  onSelect: (prompt: string) => void;
}

function getLabel(topic: QuickTopic, language: LanguageCode): string {
  if (language === "hi") return topic.labelHi;
  if (language === "mr") return topic.labelMr;
  return topic.label;
}

const QuickTopics: React.FC<Props> = ({ language, onSelect }) => {
  return (
    <div className="quick-topics" role="list" aria-label="Quick topics">
      {QUICK_TOPICS.map((topic) => (
        <button
          key={topic.id}
          className="topic-chip"
          role="listitem"
          onClick={() => onSelect(topic.prompt)}
          title={topic.prompt}
        >
          {getLabel(topic, language)}
        </button>
      ))}
    </div>
  );
};

export default QuickTopics;
