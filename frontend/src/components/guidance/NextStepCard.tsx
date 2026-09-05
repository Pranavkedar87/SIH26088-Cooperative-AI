import React from "react";
import { ArrowRightIcon, ChevronRightIcon } from "../Icons";

interface Props {
  nextSteps: string[];
  domain: string;
  onFollowUp?: (prompt: string) => void;
  language?: string;
}

export const NextStepCard: React.FC<Props> = ({
  nextSteps,
  domain,
  onFollowUp,
  language = "mr",
}) => {
  const headerTitle =
    language === "hi"
      ? "आगे क्या करें?"
      : language === "en"
      ? "What Should I Do Now?"
      : "पुढे काय करावे?";

  // Default actionable suggestions if backend didn't output explicit list
  const defaultActions: Record<string, string[]> = {
    PMFBY: [
      "जवळच्या CSC केंद्र किंवा बँकेत ७२ तासांच्या आत संपर्क साधा",
      "PMFBY पोर्टलवर ऑनलाईन अर्ज प्रक्रियेची माहिती घ्या",
    ],
    PACS: [
      "तुमच्या गावच्या PACS निबंधक / सचिवांना भेटा",
      "7/12 व आधार कार्ड सह सदस्यत्व अर्ज सादर करा",
    ],
    LAW: [
      "पोटनियमांनुसार कायदेशीर नोटीस किंवा तक्रार नोंदवा",
      "जिल्हा सहकार उपनिबंधक कार्यालय (DDR) येथे दाद मागा",
    ],
    GRIEVANCE: [
      "सहकार सेतू ऑनलाईन पोर्टलवर अधिकृत तक्रार नोंदवा",
      "तक्रारीची पोहोच व ट्रॅकिंग नंबर जतन करा",
    ],
  };

  const actionsToDisplay =
    nextSteps && nextSteps.length > 0
      ? nextSteps
      : defaultActions[domain] || [
          "या विषयावर अधिक माहितीसाठी खालील बटणावर क्लिक करा",
          "अधिकृत संकेतस्थळाला भेट द्या",
        ];

  return (
    <div className="guidance-next-steps">
      <div className="guidance-next-steps__header">
        <ArrowRightIcon size={14} color="#176B5B" />
        <span>{headerTitle}</span>
      </div>
      <div className="guidance-next-steps__list">
        {actionsToDisplay.map((act, i) => (
          <button
            key={i}
            type="button"
            className="next-step-action-btn"
            onClick={() => onFollowUp && onFollowUp(`Help me with: ${act}`)}
          >
            <span className="action-bullet">•</span>
            <span className="action-text">{act}</span>
            <ChevronRightIcon size={14} />
          </button>
        ))}
      </div>
    </div>
  );
};

export default NextStepCard;
