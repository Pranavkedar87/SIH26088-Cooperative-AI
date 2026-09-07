import React from "react";
import ConversationalAnswer from "./ConversationalAnswer";
import StructuredResponseCard from "./StructuredResponseCard";
import type { LanguageCode, SourceItem, SuggestedFollowup, StructuredAnswerData } from "../../types";

interface Props {
  rawContent: string;
  structuredAnswer?: StructuredAnswerData;
  userQuestion?: string;
  language?: string;
  answerFocus?: string;
  onExecuteAction?: (query: string) => void;
  sources?: SourceItem[];
  suggestedFollowups?: SuggestedFollowup[];
}

export const GuidanceRenderer: React.FC<Props> = ({
  rawContent,
  structuredAnswer,
  language = "mr",
  answerFocus,
  onExecuteAction,
  sources = [],
  suggestedFollowups = [],
}) => {
  if (structuredAnswer && (structuredAnswer.direct_answer || (structuredAnswer.sections && structuredAnswer.sections.length > 0))) {
    return (
      <StructuredResponseCard
        data={structuredAnswer}
        language={language as LanguageCode}
        onExecuteAction={onExecuteAction}
        sources={sources}
        suggestedFollowups={suggestedFollowups}
      />
    );
  }

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
