import React from "react";
import type { LanguageCode } from "../types";

interface SuggestedQuestion {
  en: string;
  hi: string;
  mr: string;
}

const SUGGESTED: SuggestedQuestion[] = [
  {
    en: "What services are available at PACS?",
    hi: "पैक्स (PACS) में कौन सी सेवाएं मिलती हैं?",
    mr: "PACS मध्ये कोणत्या सेवा मिळतात?",
  },
  {
    en: "How do I report crop damage under PMFBY?",
    hi: "पीएमएफबीवाई के तहत फसल नुकसान की रिपोर्ट कैसे करें?",
    mr: "पीक नुकसानीची माहिती PMFBY ला कशी द्यावी?",
  },
  {
    en: "What are the rights of a cooperative member?",
    hi: "सहकारी समिति के सदस्य के क्या अधिकार हैं?",
    mr: "सहकारी संस्थेच्या सभासदांचे अधिकार काय आहेत?",
  },
  {
    en: "How can I file a cooperative grievance?",
    hi: "सहकारी शिकायत कैसे दर्ज की जाती है?",
    mr: "सहकारी संस्थेविरुद्ध तक्रार कशी करावी?",
  },
];

const HERO_HEADING: Record<LanguageCode, string> = {
  en: "What do you need help with?",
  hi: "आपको किस विषय में सहायता चाहिए?",
  mr: "तुम्हाला कोणत्या विषयात मदत हवी आहे?",
};

const HERO_SUB: Record<LanguageCode, string> = {
  en: "Get simple, trusted guidance on cooperative laws, government schemes, PACS services, crop insurance, financial literacy and grievances.",
  hi: "सहकारी कानूनों, सरकारी योजनाओं, पैक्स सेवाओं, फसल बीमा, वित्तीय साक्षरता और शिकायतों पर सरल व विश्वसनीय मार्गदर्शन प्राप्त करें।",
  mr: "सहकारी कायदे, सरकारी योजना, पॅक्स सेवा, पीक विमा, आर्थिक साक्षरता आणि तक्रारींबाबत सुलभ व विश्वसनीय मार्गदर्शन मिळवा.",
};

interface Props {
  language: LanguageCode;
  onSelect: (question: string) => void;
}

const WelcomeHero: React.FC<Props> = ({ language, onSelect }) => {
  return (
    <section className="welcome-hero" aria-label="Assistance portal hero">
      {/* Human-scale civic assistance illustration */}
      <div className="hero-illustration" aria-hidden="true">
        <svg
          viewBox="0 0 220 120"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="hero-svg"
        >
          {/* Ground base */}
          <path d="M20 106h180" stroke="#D8D3C8" strokeWidth="2" strokeLinecap="round" />
          
          {/* Institution / Counter building */}
          <rect x="35" y="42" width="70" height="64" rx="4" fill="#FFFFFF" stroke="#145A62" strokeWidth="2" />
          <path d="M30 44l45-22 45 22" stroke="#145A62" strokeWidth="2" strokeLinejoin="round" />
          <rect x="52" y="65" width="16" height="41" fill="#E8F2F3" stroke="#145A62" strokeWidth="1.5" />
          <rect x="76" y="65" width="18" height="24" fill="#E8F2F3" stroke="#145A62" strokeWidth="1.5" />

          {/* Digital Assistance Point Pillar */}
          <rect x="135" y="55" width="30" height="51" rx="4" fill="#145A62" />
          <rect x="141" y="63" width="18" height="20" rx="2" fill="#E8F2F3" />
          <line x1="145" y1="70" x2="155" y2="70" stroke="#145A62" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="145" y1="75" x2="152" y2="75" stroke="#145A62" strokeWidth="1.5" strokeLinecap="round" />
          <circle cx="150" cy="94" r="3" fill="#D89B3D" />

          {/* Member / Farmer figure */}
          <circle cx="188" cy="62" r="7" fill="#183B4A" />
          <path d="M178 90c0-10 4-18 10-18s10 8 10 18v16h-20V90z" fill="#183B4A" />
          {/* Farmer Turban hint */}
          <path d="M182 58c2-3 8-3 12 0" stroke="#D89B3D" strokeWidth="2.5" strokeLinecap="round" />
          
          {/* Signal / Assistance Arc */}
          <path d="M172 68c-4-4-4-10 0-14" stroke="#D89B3D" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      </div>

      <div className="hero-text-block">
        <h2 className="hero-heading">{HERO_HEADING[language]}</h2>
        <p className="hero-sub">{HERO_SUB[language]}</p>
      </div>

      <div className="hero-suggestions" role="list" aria-label="Common questions">
        {SUGGESTED.map((q, idx) => (
          <button
            key={idx}
            type="button"
            className="suggestion-btn"
            role="listitem"
            onClick={() => onSelect(q[language])}
          >
            <span className="suggestion-btn__bullet">•</span>
            <span>{q[language]}</span>
          </button>
        ))}
      </div>
    </section>
  );
};

export default WelcomeHero;
