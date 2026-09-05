import React from "react";
import type { LanguageCode } from "../types";
import {
  PacsIcon,
  PmfbyIcon,
  LawIcon,
  BylawsIcon,
  SchemesIcon,
  FinanceIcon,
  GrievanceIcon,
  AgriIcon,
} from "./Icons";

interface DomainCard {
  id: string;
  icon: React.FC<{ size?: number; color?: string }>;
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
    icon: PacsIcon,
    titleEn: "PACS",
    titleHi: "पैक्स (PACS)",
    titleMr: "पॅक्स (PACS)",
    descEn: "Credit, banking & agricultural services",
    descHi: "ऋण, बैंकिंग और कृषि सेवाएं",
    descMr: "कर्ज, बँकिंग व कृषी सेवा",
    promptEn: "What services are available at PACS?",
  },
  {
    id: "pmfby",
    icon: PmfbyIcon,
    titleEn: "PMFBY",
    titleHi: "पीएमएफबीवाई",
    titleMr: "पीएमएफबीवाय (PMFBY)",
    descEn: "Crop insurance & damage compensation",
    descHi: "फसल बीमा और क्षति मुआवजा",
    descMr: "पीक विमा व नुकसान भरपाई",
    promptEn: "Explain the Pradhan Mantri Fasal Bima Yojana (PMFBY) scheme.",
  },
  {
    id: "cooperative_law",
    icon: LawIcon,
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
    icon: BylawsIcon,
    titleEn: "By-laws",
    titleHi: "उप-नियम",
    titleMr: "उपविधी",
    descEn: "Member rights & governance rules",
    descHi: "सदस्य अधिकार एवं संचालन नियम",
    descMr: "सदस्य हक्क व व्यवस्थापन नियम",
    promptEn: "Explain the standard by-laws for a cooperative society.",
  },
  {
    id: "schemes",
    icon: SchemesIcon,
    titleEn: "Government Schemes",
    titleHi: "सरकारी योजनाएं",
    titleMr: "सरकारी योजना",
    descEn: "Welfare & development schemes",
    descHi: "कल्याणकारी एवं विकास योजनाएं",
    descMr: "कल्याणकारी व विकास योजना",
    promptEn: "What government schemes are available for cooperative societies?",
  },
  {
    id: "financial_literacy",
    icon: FinanceIcon,
    titleEn: "Financial Literacy",
    titleHi: "वित्तीय साक्षरता",
    titleMr: "आर्थिक साक्षरता",
    descEn: "Credit guidance & money management",
    descHi: "ऋण मार्गदर्शन एवं धन प्रबंधन",
    descMr: "कर्ज मार्गदर्शन व आर्थिक नियोजन",
    promptEn: "Give me basic financial literacy tips for cooperative members.",
  },
  {
    id: "grievance",
    icon: GrievanceIcon,
    titleEn: "Grievance Redressal",
    titleHi: "शिकायत निवारण",
    titleMr: "तक्रार निवारण",
    descEn: "Complaint mechanisms & member rights",
    descHi: "शिकायत प्रक्रिया एवं सदस्य अधिकार",
    descMr: "तक्रार प्रक्रिया व सदस्य अधिकार",
    promptEn: "How do I file a grievance against a cooperative society?",
  },
  {
    id: "agri_support",
    icon: AgriIcon,
    titleEn: "Agricultural Support",
    titleHi: "कृषि सहायता",
    titleMr: "शेती सहाय्य",
    descEn: "Crop damage & farming assistance",
    descHi: "फसल क्षति एवं कृषि सहायता",
    descMr: "पीक नुकसान व शेती मदत",
    promptEn: "What to do in case of heavy rain soybean crop damage?",
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
    <div className="domain-cards-grid" role="list" aria-label="Explore Services">
      {DOMAIN_CARDS.map((card) => {
        const IconComponent = card.icon;
        return (
          <button
            key={card.id}
            type="button"
            className="service-card"
            role="listitem"
            onClick={() => onSelect(card.promptEn)}
            aria-label={`Select ${card.titleEn}`}
          >
            <div className="service-card__icon-box">
              <IconComponent size={20} color="#145A62" />
            </div>
            <div className="service-card__content">
              <span className="service-card__title">{getTitle(card)}</span>
              <span className="service-card__desc">{getDesc(card)}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
};

export default DomainCards;
