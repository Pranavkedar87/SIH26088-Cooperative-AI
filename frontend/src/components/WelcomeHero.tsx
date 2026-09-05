import React from "react";
import type { LanguageCode } from "../types";

interface SuggestedQuestion {
  en: string;
  hi: string;
  mr: string;
}

const SUGGESTED: SuggestedQuestion[] = [
  {
    en: "How do PACS help farmers?",
    hi: "पैक्स किसानों की मदद कैसे करती है?",
    mr: "पॅक्स शेतकऱ्यांना कशी मदत करते?",
  },
  {
    en: "Explain PMFBY crop insurance",
    hi: "पीएमएफबीवाई फसल बीमा समझाएं",
    mr: "PMFBY पीक विमा योजना सांगा",
  },
  {
    en: "What is the Cooperative Societies Act?",
    hi: "सहकारी समिति अधिनियम क्या है?",
    mr: "सहकारी संस्था कायदा काय आहे?",
  },
  {
    en: "How to file a cooperative grievance?",
    hi: "सहकारी शिकायत कैसे दर्ज करें?",
    mr: "सहकारी तक्रार कशी नोंदवावी?",
  },
  {
    en: "What is financial literacy for farmers?",
    hi: "किसानों के लिए वित्तीय साक्षरता क्या है?",
    mr: "शेतकऱ्यांसाठी आर्थिक साक्षरता म्हणजे काय?",
  },
  {
    en: "Services available at PACS",
    hi: "पैक्स में उपलब्ध सेवाएं",
    mr: "PACS मध्ये कोणत्या सेवा मिळतात?",
  },
];

const HERO_HEADING: Record<LanguageCode, string> = {
  en: "How can we help you today?",
  hi: "आज हम आपकी कैसे मदद कर सकते हैं?",
  mr: "आज आम्ही तुम्हाला कशी मदत करू शकतो?",
};

const HERO_SUB: Record<LanguageCode, string> = {
  en: "Trusted multilingual AI for cooperative members, farmers & rural stakeholders",
  hi: "सहकारी सदस्यों, किसानों और ग्रामीण हितधारकों के लिए विश्वसनीय बहुभाषी AI",
  mr: "सहकारी सदस्य, शेतकरी आणि ग्रामीण भागधारकांसाठी विश्वसनीय बहुभाषी AI",
};

interface Props {
  language: LanguageCode;
  onSelect: (question: string) => void;
}

const WelcomeHero: React.FC<Props> = ({ language, onSelect }) => {
  return (
    <section className="welcome-hero" aria-label="Welcome hero">
      {/* Lightweight cooperative SVG illustration */}
      <div className="hero-illustration" aria-hidden="true">
        <svg
          viewBox="0 0 200 160"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="hero-svg"
          role="img"
          aria-label="Cooperative handshake illustration"
        >
          {/* Ground */}
          <ellipse cx="100" cy="148" rx="80" ry="10" fill="#d4e9d4" />
          {/* Wheat stalks */}
          <g stroke="#8fb85a" strokeWidth="2">
            <line x1="55" y1="148" x2="55" y2="90" />
            <line x1="55" y1="90" x2="50" y2="78" />
            <line x1="55" y1="90" x2="60" y2="78" />
            <line x1="55" y1="100" x2="47" y2="92" />
            <line x1="55" y1="100" x2="63" y2="92" />
            <line x1="145" y1="148" x2="145" y2="90" />
            <line x1="145" y1="90" x2="140" y2="78" />
            <line x1="145" y1="90" x2="150" y2="78" />
            <line x1="145" y1="100" x2="137" y2="92" />
            <line x1="145" y1="100" x2="153" y2="92" />
          </g>
          {/* Handshake icon — left hand */}
          <path
            d="M72 105 Q65 95 72 88 L88 80 Q92 78 95 82 L100 90"
            stroke="#1a5f7a"
            strokeWidth="3.5"
            strokeLinecap="round"
            fill="none"
          />
          {/* Right hand */}
          <path
            d="M128 105 Q135 95 128 88 L112 80 Q108 78 105 82 L100 90"
            stroke="#e67e22"
            strokeWidth="3.5"
            strokeLinecap="round"
            fill="none"
          />
          {/* Clasped hands center */}
          <ellipse cx="100" cy="100" rx="14" ry="10" fill="#1a5f7a" opacity="0.15" />
          <path
            d="M88 98 Q94 94 100 96 Q106 94 112 98 Q106 104 100 106 Q94 104 88 98Z"
            fill="#1a5f7a"
          />
          {/* Cooperation text arc glyph */}
          <circle cx="100" cy="55" r="22" stroke="#e67e22" strokeWidth="2" fill="#fff8f0" />
          <text x="100" y="60" textAnchor="middle" fontSize="18" fill="#e67e22">🤝</text>
        </svg>
      </div>

      {/* Heading */}
      <h2 className="hero-heading">{HERO_HEADING[language]}</h2>
      <p className="hero-sub">{HERO_SUB[language]}</p>

      {/* Suggested questions */}
      <div className="hero-suggestions" role="list" aria-label="Suggested questions">
        {SUGGESTED.map((q, idx) => (
          <button
            key={idx}
            type="button"
            className="suggestion-chip"
            role="listitem"
            onClick={() => onSelect(q[language])}
          >
            {q[language]}
          </button>
        ))}
      </div>
    </section>
  );
};

export default WelcomeHero;
