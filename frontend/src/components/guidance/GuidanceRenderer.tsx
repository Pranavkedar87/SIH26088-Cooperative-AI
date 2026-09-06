import React from "react";
import { parseGuidance, type StructuredGuidance } from "../../utils/guidanceParser";
import KeyFactCard from "./KeyFactCard";
import StepTimeline from "./StepTimeline";
import Checklist from "./Checklist";
import WarningCard from "./WarningCard";
import NextStepCard from "./NextStepCard";
import ConversationalAnswer from "./ConversationalAnswer";
import type { LanguageCode } from "../../types";
import { ShieldCheckIcon, ExternalLinkIcon } from "../Icons";

interface Props {
  rawContent: string;
  userQuestion?: string;
  language?: string;
  answerFocus?: string;
  onExecuteAction?: (query: string) => void;
  sources?: Array<{ title: string; source_name?: string | null; source_url?: string | null; document_id?: string | null }>;
}

export const GuidanceRenderer: React.FC<Props> = ({
  rawContent,
  userQuestion,
  language = "mr",
  answerFocus,
  onExecuteAction,
  sources = [],
}) => {
  const guidance: StructuredGuidance = parseGuidance(rawContent, language, answerFocus);
  const lang = language as LanguageCode;

  // Localized section headers matching the SahkaarSetu Guidance Note layout
  const docTitle =
    lang === "hi"
      ? "सहकार सेतू - आधिकारिक मार्गदर्शन नोट"
      : lang === "en"
      ? "SahkaarSetu Official Guidance Note"
      : "सहकार सेतू - अधिकृत मार्गदर्शन नोंद";

  const userQuestionLabel =
    lang === "hi"
      ? "आपका प्रश्न / विषय:"
      : lang === "en"
      ? "YOUR QUESTION / TOPIC:"
      : "आपला प्रश्न / विषय:";

  const guidanceOverviewLabel =
    lang === "hi"
      ? "मार्गदर्शन एवं विवरण:"
      : lang === "en"
      ? "OFFICIAL GUIDANCE & DETAILS:"
      : "अधिकृत मार्गदर्शन व माहिती:";

  const keyFactsLabel =
    lang === "hi"
      ? "मुख्य विवरण एवं दरें:"
      : lang === "en"
      ? "KEY HIGHLIGHTS & DETAILS:"
      : "महत्त्वाचे तपशील व दर:";

  const sourcesLabel =
    lang === "hi"
      ? "अधिकृत स्रोत एवं संदर्भ:"
      : lang === "en"
      ? "OFFICIAL SOURCES & REFERENCES:"
      : "अधिकृत स्रोत व संदर्भ:";

  return (
    <div className="guidance-system guidance-note-layout">
      {/* 1. Header Row with Domain Pill */}
      <div className="guidance-note-top-bar">
        <div className="guidance-note-brand">
          <span className="guidance-note-title">SAHKAARSETU</span>
          <span className="guidance-note-subtitle">
            {lang === "hi"
              ? "बहुभाषी सहकार सहायता मंच"
              : lang === "en"
              ? "Multilingual Cooperative Assistance Platform"
              : "बहुभाषिक सहकार मदत व्यासपीठ"}
          </span>
        </div>
        {guidance.domainLabel && (
          <div className="guidance-domain-pill">
            <ShieldCheckIcon size={14} color="#126B62" />
            <span>{guidance.domainLabel}</span>
          </div>
        )}
      </div>

      {/* 2. Official Guidance Note Banner */}
      <div className="guidance-note-banner">
        <h2>{docTitle}</h2>
      </div>

      {/* 3. User Question Callout Box */}
      {userQuestion && (
        <div className="guidance-question-box">
          <div className="guidance-question-label">{userQuestionLabel}</div>
          <div className="guidance-question-text">"{userQuestion}"</div>
        </div>
      )}

      {/* 4. Guidance Overview Section */}
      <div className="guidance-section">
        <div className="guidance-section-heading">{guidanceOverviewLabel}</div>
        <ConversationalAnswer
          content={rawContent}
          language={lang}
          answerFocus={answerFocus}
          onExecuteAction={onExecuteAction}
        />
      </div>

      {/* 5. Key Facts & Highlights Grid */}
      {guidance.keyFacts.length > 0 && (
        <div className="guidance-section">
          <div className="guidance-section-heading">{keyFactsLabel}</div>
          <KeyFactCard facts={guidance.keyFacts} language={language} answerFocus={answerFocus} />
        </div>
      )}

      {/* 6. Step-by-Step Procedure Timeline */}
      {guidance.steps.length > 0 && (
        <StepTimeline steps={guidance.steps} language={language} />
      )}

      {/* 7. Warnings & Requirements Checklist */}
      {guidance.warnings.length > 0 && (
        <WarningCard warnings={guidance.warnings} language={language} />
      )}
      {guidance.checklist.length > 0 && (
        <Checklist items={guidance.checklist} language={language} />
      )}

      {/* 8. Next Step Action Buttons */}
      <NextStepCard
        actions={guidance.nextActions}
        onExecuteAction={onExecuteAction}
        language={language}
      />

      {/* 9. Official Sources & References */}
      {sources && sources.length > 0 && (
        <div className="guidance-section guidance-sources-section">
          <div className="guidance-section-heading">{sourcesLabel}</div>
          <ul className="guidance-sources-list">
            {sources.map((src, i) => (
              <li key={i} className="guidance-source-item">
                <span className="source-bullet">•</span>
                <span className="source-title">{src.title}</span>
                {src.source_name && <span className="source-authority"> ({src.source_name})</span>}
                {src.source_url && (
                  <a
                    href={src.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-link"
                  >
                    <ExternalLinkIcon size={12} color="#126B62" />
                  </a>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 10. Footer Tag */}
      <div className="guidance-note-footer">
        <span>SahkaarSetu • Understand. Get Guided. Move Forward.</span>
      </div>
    </div>
  );
};

export default GuidanceRenderer;
