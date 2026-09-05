import React from "react";
import type { LanguageCode } from "../types";
import {
  WheatIcon,
  LandmarkIcon,
  ScaleIcon,
  WalletCardsIcon,
  FileCheckIcon,
  ClipboardCheckIcon,
  MessageSquareIcon,
  ArrowRightIcon,
  MicIcon,
} from "./Icons";

interface Props {
  language: LanguageCode;
  onStartAsk: (initialQuery?: string) => void;
  onSelectGuided: (flowType: string) => void;
  onSelectService: (serviceId: string) => void;
  isListening?: boolean;
  onMicClick?: () => void;
}

const GREETINGS: Record<
  LanguageCode,
  { title: string; subtitle: string; askBtn: string; guidedBtn: string; helpHeader: string }
> = {
  en: {
    title: "Namaskar",
    subtitle: "How can SahkaarSetu help you today?",
    askBtn: "Ask SahkaarSetu",
    guidedBtn: "Get Guided Help",
    helpHeader: "What do you need help with?",
  },
  hi: {
    title: "नमस्कार",
    subtitle: "आज सहकारसेतु आपकी क्या सहायता कर सकता है?",
    askBtn: "सहकारसेतु से प्रश्न पूछें",
    guidedBtn: "मार्गदर्शित सहायता प्राप्त करें",
    helpHeader: "आपको किस विषय में सहायता चाहिए?",
  },
  mr: {
    title: "नमस्कार",
    subtitle: "आज सहकारसेतू तुम्हाला कशी मदत करू शकते?",
    askBtn: "सहकारसेतूला प्रश्न विचारा",
    guidedBtn: "मार्गदर्शित मदत घ्या",
    helpHeader: "तुम्हाला कोणत्या विषयात मदत हवी आहे?",
  },
};

const SERVICE_CARDS: Array<{
  id: string;
  icon: React.FC<{ size?: number; color?: string }>;
  en: string;
  hi: string;
  mr: string;
  descEn: string;
  descHi: string;
  descMr: string;
}> = [
  {
    id: "crop_damage",
    icon: WheatIcon,
    en: "Crop & Insurance",
    hi: "फसल और बीमा",
    mr: "पीक आणि विमा",
    descEn: "Understand PMFBY crop insurance and damage compensation",
    descHi: "पीएमएफबीवाई फसल बीमा और मुआवजा सहायता समझें",
    descMr: "PMFBY पीक विमा व मदत मार्गदर्शन समजून घ्या",
  },
  {
    id: "pacs_help",
    icon: LandmarkIcon,
    en: "PACS Services",
    hi: "पैक्स सेवाएं",
    mr: "पॅक्स सेवा",
    descEn: "Get guidance on PACS credit, fertilizer, and warehouse services",
    descHi: "पैक्स ऋण, उर्वरक और गोदाम सेवाओं पर मार्गदर्शन पाएं",
    descMr: "PACS कर्ज, खते व गोदाम सेवांबाबत मार्गदर्शन मिळवा",
  },
  {
    id: "coop_rule",
    icon: ScaleIcon,
    en: "Cooperative Rules",
    hi: "सहकारी नियम",
    mr: "सहकारी नियम",
    descEn: "Understand Maharashtra Cooperative laws and model by-laws",
    descHi: "महाराष्ट्र सहकारी कानून और मॉडल उपनियम समझें",
    descMr: "महाराष्ट्र सहकारी संस्था कायदा व उपविधी समजून घ्या",
  },
  {
    id: "financial_guidance",
    icon: WalletCardsIcon,
    en: "Financial Guidance",
    hi: "वित्तीय मार्गदर्शन",
    mr: "आर्थिक मार्गदर्शन",
    descEn: "Understand KCC loans, interest subvention, and savings",
    descHi: "केसीसी ऋण, ब्याज अनुदान और बचत मार्गदर्शन",
    descMr: "KCC कर्ज, व्याज सवलत व बचत मार्गदर्शन",
  },
  {
    id: "schemes_entry",
    icon: FileCheckIcon,
    en: "Government Schemes",
    hi: "सरकारी योजनाएं",
    mr: "सरकारी योजना",
    descEn: "Explore Ministry of Cooperation development schemes",
    descHi: "सहकार मंत्रालय की विकास योजनाओं की जानकारी पाएं",
    descMr: "सहकार मंत्रालयाच्या विकास योजनांची माहिती घ्या",
  },
  {
    id: "grievance_entry",
    icon: ClipboardCheckIcon,
    en: "Grievance Assistance",
    hi: "शिकायत सहायता",
    mr: "तक्रार सहाय्य",
    descEn: "Understand complaint steps and generate formal summaries",
    descHi: "शिकायत प्रक्रिया समझें और औपचारिक सारांश बनाएं",
    descMr: "तक्रार प्रक्रिया समजून घ्या व सारांश तयार करा",
  },
];

const AssistanceHub: React.FC<Props> = ({
  language,
  onStartAsk,
  onSelectGuided,
  isListening = false,
  onMicClick,
}) => {
  const locale = GREETINGS[language];

  return (
    <div className="assistance-hub" aria-label="SahkaarSetu Assistance Hub">
      {/* Hero Welcome Section */}
      <section className="hub-hero">
        <div className="hub-hero__content">
          <h2 className="hub-hero__greeting">{locale.title}</h2>
          <h3 className="hub-hero__question">{locale.subtitle}</h3>
          <p className="hub-hero__text">
            {language === "hi"
              ? "सहकारी कानूनों, योजनाओं, पैक्स, फसल बीमा और शिकायतों पर विश्वसनीय मार्गदर्शन प्राप्त करें।"
              : language === "mr"
              ? "सहकारी कायदे, योजना, पॅक्स, पीक विमा आणि तक्रारींबाबत सुलभ मार्गदर्शन मिळवा."
              : "Get trusted guidance on cooperatives, schemes, PACS, crop insurance and grievances."}
          </p>

          {/* Primary Action Buttons */}
          <div className="hub-hero__primary-ctas">
            <button
              type="button"
              className="cta-btn cta-btn--primary"
              onClick={() => onStartAsk()}
            >
              <MessageSquareIcon size={18} color="#FFFFFF" />
              <span>{locale.askBtn}</span>
            </button>

            <button
              type="button"
              className="cta-btn cta-btn--secondary"
              onClick={() => onSelectGuided("crop_damage")}
            >
              <ArrowRightIcon size={18} color="#176B5B" />
              <span>{locale.guidedBtn}</span>
            </button>

            {onMicClick && (
              <button
                type="button"
                className={`voice-shortcut-btn ${isListening ? "voice-shortcut-btn--active" : ""}`}
                onClick={onMicClick}
                aria-label="Voice Input"
                title="Voice Input"
              >
                <MicIcon size={18} color={isListening ? "#B94A48" : "#176B5B"} />
                <span>{isListening ? "Listening…" : "Voice"}</span>
              </button>
            )}
          </div>
        </div>
      </section>

      {/* Guided Service Cards Directory */}
      <section className="hub-services-section">
        <h3 className="hub-services__title">{locale.helpHeader}</h3>

        <div className="hub-services-grid" role="list">
          {SERVICE_CARDS.map((card) => {
            const IconComp = card.icon;
            const title = card[language] ?? card.en;
            const desc =
              language === "hi"
                ? card.descHi
                : language === "mr"
                ? card.descMr
                : card.descEn;

            return (
              <button
                key={card.id}
                type="button"
                className="hub-service-card"
                role="listitem"
                onClick={() => onSelectGuided(card.id)}
              >
                <div className="hub-service-card__icon">
                  <IconComp size={22} color="#176B5B" />
                </div>
                <div className="hub-service-card__body">
                  <span className="hub-service-card__title">{title}</span>
                  <span className="hub-service-card__desc">{desc}</span>
                </div>
                <div className="hub-service-card__arrow">
                  <ArrowRightIcon size={14} color="#66777A" />
                </div>
              </button>
            );
          })}
        </div>
      </section>
    </div>
  );
};

export default AssistanceHub;
