import React, { useState } from "react";
import type { LanguageCode } from "../types";
import {
  WheatIcon,
  LandmarkIcon,
  ScaleIcon,
  WalletCardsIcon,
  FileCheckIcon,
  ClipboardCheckIcon,
  ArrowRightIcon,
  MicIcon,
  SendIcon,
  ShieldCheckIcon,
} from "./Icons";

interface Props {
  language: LanguageCode;
  onStartAsk: (initialQuery?: string) => void;
  onOpenVoiceMode: () => void;
  onSelectGuided: (flowType: string) => void;
}

const HERO_TEXT: Record<
  string,
  { headline: string; sub: string; voiceBtn: string; typeOr: string; placeholder: string; helpHeader: string; helpSub: string }
> = {
  mr: {
    headline: "सहकारी सेवांसाठी तुमचा डिजिटल साथी",
    sub: "समजून घ्या • विचारा • पुढील पाऊल जाणून घ्या",
    voiceBtn: "बोलून विचारा",
    typeOr: "किंवा प्रश्न टाइप करा",
    placeholder: "सहकारी सेवा, योजना किंवा कायद्याबद्दल विचारा...",
    helpHeader: "तुम्हाला कशाबद्दल मदत हवी आहे?",
    helpSub: "तुमची समस्या निवडा किंवा SahkaarSetu ला बोलून सांगा.",
  },
  hi: {
    headline: "सहकारी सेवाओं के लिए आपका डिजिटल साथी",
    sub: "समझें • पूछें • अगला कदम जानें",
    voiceBtn: "बोलकर पूछें",
    typeOr: "या प्रश्न टाइप करें",
    placeholder: "सहकारी सेवाओं, योजनाओं या कानून के बारे में पूछें...",
    helpHeader: "आपको किस विषय में सहायता चाहिए?",
    helpSub: "अपनी समस्या चुनें या SahkaarSetu से बोलकर कहें।",
  },
  en: {
    headline: "Your Digital Companion for Cooperative Services",
    sub: "Understand • Ask • Know Next Steps",
    voiceBtn: "Speak to SahkaarSetu",
    typeOr: "or type your question",
    placeholder: "Ask about cooperative services, schemes or laws...",
    helpHeader: "What do you need help with?",
    helpSub: "Select a topic or speak to SahkaarSetu directly.",
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
    descEn: "PMFBY crop insurance and damage guidance",
    descHi: "पीएमएफबीवाई फसल बीमा और मुआवजा सहायता",
    descMr: "PMFBY पीक विमा व नुकसान मार्गदर्शन",
  },
  {
    id: "pacs_help",
    icon: LandmarkIcon,
    en: "PACS Services",
    hi: "पैक्स सेवाएं",
    mr: "पॅक्स सेवा",
    descEn: "PACS credit, fertilizer, and member loans",
    descHi: "पैक्स ऋण, उर्वरक और किसान सेवाएं",
    descMr: "कर्ज, खते, बियाणे व सोसायटी सेवा",
  },
  {
    id: "coop_rule",
    icon: ScaleIcon,
    en: "Cooperative Rules",
    hi: "सहकारी नियम",
    mr: "सहकारी कायदे",
    descEn: "Maharashtra Cooperative laws and by-laws",
    descHi: "महाराष्ट्र सहकारी कानून और मॉडल उपनियम",
    descMr: "कायदा, पोटनियम व कायदेशीर सल्ला",
  },
  {
    id: "financial_guidance",
    icon: WalletCardsIcon,
    en: "Financial Literacy",
    hi: "वित्तीय साक्षरता",
    mr: "आर्थिक साक्षरता",
    descEn: "KCC loans, interest subvention, and savings",
    descHi: "केसीसी ऋण, ब्याज अनुदान और बचत मार्गदर्शन",
    descMr: "आर्थिक साक्षरता, KCC व कर्ज सवलत",
  },
  {
    id: "schemes_entry",
    icon: FileCheckIcon,
    en: "Government Schemes",
    hi: "सरकारी योजनाएं",
    mr: "सरकारी योजना",
    descEn: "Ministry of Cooperation development schemes",
    descHi: "सहकार मंत्रालय की विकास योजनाएं",
    descMr: "सहकार मंत्रालयाच्या विकास योजना",
  },
  {
    id: "grievance_entry",
    icon: ClipboardCheckIcon,
    en: "Grievance Assistance",
    hi: "शिकायत सहायता",
    mr: "तक्रार निवारण",
    descEn: "Complaint steps and formal summary builder",
    descHi: "शिकायत प्रक्रिया और औपचारिक सारांश",
    descMr: "तक्रार निवारण मदत व मसुदा मार्गदर्शक",
  },
];

const AssistanceHub: React.FC<Props> = ({
  language,
  onStartAsk,
  onOpenVoiceMode,
  onSelectGuided,
}) => {
  const t = HERO_TEXT[language] ?? HERO_TEXT.en;
  const [typedInput, setTypedInput] = useState("");

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (typedInput.trim()) {
      onStartAsk(typedInput.trim());
      setTypedInput("");
    }
  };

  return (
    <div className="assistance-hub" aria-label="SahkaarSetu Assistance Hub">
      {/* Hero Section */}
      <section className="hub-hero">
        <div className="hub-hero__content">
          <h2 className="hub-hero__headline">{t.headline}</h2>
          <p className="hub-hero__sub">{t.sub}</p>

          {/* PRIMARY VOICE CTA */}
          <button
            type="button"
            className="hero-voice-cta"
            onClick={onOpenVoiceMode}
            aria-label="Start Voice Assistance"
          >
            <div className="hero-voice-cta__icon">
              <MicIcon size={24} color="#FFFFFF" />
            </div>
            <div className="hero-voice-cta__text">
              <span className="cta-main-label">{t.voiceBtn}</span>
              <span className="cta-sub-label">Hindi • Marathi • English</span>
            </div>
          </button>

          {/* SECONDARY TEXT INPUT */}
          <div className="hero-secondary-input">
            <span className="secondary-label">{t.typeOr}</span>
            <form onSubmit={handleTextSubmit} className="secondary-search-bar">
              <input
                type="text"
                className="secondary-search-input"
                value={typedInput}
                onChange={(e) => setTypedInput(e.target.value)}
                placeholder={t.placeholder}
              />
              <button
                type="submit"
                className="secondary-search-btn"
                disabled={!typedInput.trim()}
                aria-label="Submit Question"
              >
                <SendIcon size={16} color="#FFFFFF" />
              </button>
            </form>
          </div>
        </div>
      </section>

      {/* Service Directory Section */}
      <section className="hub-services-section">
        <div className="hub-services-header">
          <h3 className="hub-services__title">{t.helpHeader}</h3>
          <p className="hub-services__sub">{t.helpSub}</p>
        </div>

        <div className="hub-services-grid" role="list">
          {SERVICE_CARDS.map((card) => {
            const IconComp = card.icon;
            const title = (card as any)[language] ?? card.en;
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
                  <IconComp size={20} color="#126B62" />
                </div>
                <div className="hub-service-card__body">
                  <span className="hub-service-card__title">{title}</span>
                  <span className="hub-service-card__desc">{desc}</span>
                </div>
                <div className="hub-service-card__arrow">
                  <ArrowRightIcon size={14} color="#667875" />
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* Trust Element Footer Note */}
      <footer className="hub-trust-footer">
        <div className="trust-item">
          <ShieldCheckIcon size={14} color="#126B62" />
          <span>Source-backed guidance</span>
        </div>
        <span className="trust-dot">•</span>
        <div className="trust-item">
          <span>Hindi • Marathi • English</span>
        </div>
        <span className="trust-dot">•</span>
        <div className="trust-item">
          <span>Cooperative Assistance</span>
        </div>
      </footer>
    </div>
  );
};

export default AssistanceHub;
