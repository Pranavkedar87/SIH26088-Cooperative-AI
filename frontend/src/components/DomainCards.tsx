import React from "react";
import type { LanguageCode } from "../types";

interface DomainCard {
  id: string;
  icon: string;
  titleEn: string;
  titleHi: string;
  titleMr: string;
  descEn: string;
  descHi: string;
  descMr: string;
  promptEn: string;
}

const DOMAIN_CARDS: DomainCard[] = [
  {
    id: "pacs",
    icon: "🏦",
    titleEn: "PACS",
    titleHi: "पैक्स",
    titleMr: "पॅक्स",
    descEn: "Credit & banking for farmers",
    descHi: "किसानों के लिए ऋण और बैंकिंग",
    descMr: "शेतकऱ्यांसाठी कर्ज आणि बँकिंग",
    promptEn: "What services are available at PACS?",
  },
  {
    id: "pmfby",
    icon: "🌾",
    titleEn: "PMFBY",
    titleHi: "पीएमएफबीवाई",
    titleMr: "पीएमएफबीवाय",
    descEn: "Pradhan Mantri crop insurance",
    descHi: "प्रधानमंत्री फसल बीमा योजना",
    descMr: "प्रधानमंत्री पीक विमा योजना",
    promptEn: "Explain the Pradhan Mantri Fasal Bima Yojana (PMFBY) scheme.",
  },
  {
    id: "cooperative_law",
    icon: "⚖️",
    titleEn: "Cooperative Law",
    titleHi: "सहकारी कानून",
    titleMr: "सहकारी कायदा",
    descEn: "Maharashtra Cooperative Societies Act",
    descHi: "महाराष्ट्र सहकारी समिति अधिनियम",
    descMr: "महाराष्ट्र सहकारी संस्था कायदा",
    promptEn: "What are the key provisions of the Maharashtra Cooperative Societies Act?",
  },
  {
    id: "bylaws",
    icon: "📜",
    titleEn: "By-laws",
    titleHi: "उपनियम",
    titleMr: "उपविधी",
    descEn: "Standard cooperative by-laws",
    descHi: "मानक सहकारी उपनियम",
    descMr: "मानक सहकारी उपविधी",
    promptEn: "Explain the standard by-laws for a cooperative society.",
  },
  {
    id: "schemes",
    icon: "🏛️",
    titleEn: "Schemes",
    titleHi: "योजनाएं",
    titleMr: "योजना",
    descEn: "Government schemes for cooperatives",
    descHi: "सहकारी समितियों के लिए सरकारी योजनाएं",
    descMr: "सहकारींसाठी सरकारी योजना",
    promptEn: "What government schemes are available for cooperative societies?",
  },
  {
    id: "financial_literacy",
    icon: "💰",
    titleEn: "Financial Literacy",
    titleHi: "वित्तीय साक्षरता",
    titleMr: "आर्थिक साक्षरता",
    descEn: "Money management for members",
    descHi: "सदस्यों के लिए धन प्रबंधन",
    descMr: "सदस्यांसाठी आर्थिक व्यवस्थापन",
    promptEn: "Give me basic financial literacy tips for cooperative members.",
  },
  {
    id: "grievance",
    icon: "📋",
    titleEn: "Grievance",
    titleHi: "शिकायत",
    titleMr: "तक्रार",
    descEn: "File & track your complaint",
    descHi: "अपनी शिकायत दर्ज करें और ट्रैक करें",
    descMr: "तुमची तक्रार नोंदवा व ट्रॅक करा",
    promptEn: "How do I file a grievance against a cooperative society?",
  },
  {
    id: "digital_banking",
    icon: "🏧",
    titleEn: "Digital Banking",
    titleHi: "डिजिटल बैंकिंग",
    titleMr: "डिजिटल बँकिंग",
    descEn: "Online banking for rural members",
    descHi: "ग्रामीण सदस्यों के लिए ऑनलाइन बैंकिंग",
    descMr: "ग्रामीण सदस्यांसाठी ऑनलाइन बँकिंग",
    promptEn: "How can cooperative members use digital banking services?",
  },
];

interface Props {
  language: LanguageCode;
  onSelect: (prompt: string) => void;
}

const DomainCards: React.FC<Props> = ({ language, onSelect }) => {
  const getTitle = (card: DomainCard) => {
    if (language === "hi") return card.titleHi;
    if (language === "mr") return card.titleMr;
    return card.titleEn;
  };

  const getDesc = (card: DomainCard) => {
    if (language === "hi") return card.descHi;
    if (language === "mr") return card.descMr;
    return card.descEn;
  };

  return (
    <div className="domain-cards" role="list" aria-label="Domain categories">
      {DOMAIN_CARDS.map((card) => (
        <button
          key={card.id}
          type="button"
          className="domain-card"
          role="listitem"
          onClick={() => onSelect(card.promptEn)}
          aria-label={`Ask about ${card.titleEn}`}
        >
          <span className="domain-card__icon" aria-hidden="true">{card.icon}</span>
          <span className="domain-card__title">{getTitle(card)}</span>
          <span className="domain-card__desc">{getDesc(card)}</span>
        </button>
      ))}
    </div>
  );
};

export default DomainCards;
