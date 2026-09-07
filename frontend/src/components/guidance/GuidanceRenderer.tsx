import React from "react";
import ConversationalAnswer from "./ConversationalAnswer";
import type { LanguageCode, SourceItem, SuggestedFollowup } from "../../types";

interface Props {
  rawContent: string;
  userQuestion?: string;
  language?: string;
  answerFocus?: string;
  onExecuteAction?: (query: string) => void;
  sources?: SourceItem[];
  suggestedFollowups?: SuggestedFollowup[];
}

export const GuidanceRenderer: React.FC<Props> = ({
  rawContent,
  language = "mr",
  answerFocus,
  onExecuteAction,
  sources = [],
  suggestedFollowups = [],
}) => {
  return (
    <ConversationalAnswer
      content={rawContent}
      language={language as LanguageCode}
      answerFocus={answerFocus}
      onExecuteAction={onExecuteAction}
      sources={sources}
      suggestedFollowups={suggestedFollowups}
    />
  );
};

export default GuidanceRenderer;
