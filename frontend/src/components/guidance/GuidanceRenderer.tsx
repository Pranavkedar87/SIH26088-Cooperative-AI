import React from "react";
import ConversationalAnswer from "./ConversationalAnswer";
import type { LanguageCode, SourceItem } from "../../types";

interface Props {
  rawContent: string;
  userQuestion?: string;
  language?: string;
  answerFocus?: string;
  onExecuteAction?: (query: string) => void;
  sources?: SourceItem[];
}

export const GuidanceRenderer: React.FC<Props> = ({
  rawContent,
  language = "mr",
  answerFocus,
  onExecuteAction,
  sources = [],
}) => {
  return (
    <ConversationalAnswer
      content={rawContent}
      language={language as LanguageCode}
      answerFocus={answerFocus}
      onExecuteAction={onExecuteAction}
      sources={sources}
    />
  );
};

export default GuidanceRenderer;
