import React from "react";
import GuidanceRenderer from "./guidance/GuidanceRenderer";
import type { AnswerSection } from "../utils/parseAnswer";

interface Props {
  sections?: AnswerSection[];
  rawText?: string;
  language?: string;
  onFollowUp?: (prompt: string) => void;
}

const StructuredAnswer: React.FC<Props> = ({ rawText = "", language = "mr", onFollowUp }) => {
  return (
    <GuidanceRenderer
      rawContent={rawText}
      language={language}
      onExecuteAction={onFollowUp}
    />
  );
};

export default StructuredAnswer;
