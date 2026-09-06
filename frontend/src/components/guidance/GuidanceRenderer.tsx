import React from "react";
import ConversationalAnswer from "./ConversationalAnswer";
import type { LanguageCode } from "../../types";

interface Props {
  rawContent: string;
  userQuestion?: string;
  language?: string;
  answerFocus?: string;
  onExecuteAction?: (query: string) => void;
  sources?: Array<{ title: string; authority?: string; url?: string }>;
}

export const GuidanceRenderer: React.FC<Props> = ({
  rawContent,
  language = "mr",
  answerFocus,
  onExecuteAction,
}) => {
  return (
    <ConversationalAnswer
      content={rawContent}
      language={language as LanguageCode}
      answerFocus={answerFocus}
      onExecuteAction={onExecuteAction}
    />
  );
};

export default GuidanceRenderer;
