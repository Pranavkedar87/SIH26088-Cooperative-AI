import React, { useState } from "react";
import type { LanguageCode } from "../types";
import { MicIcon, SendIcon } from "./Icons";

interface Props {
  language: LanguageCode;
  onStartAsk: (initialQuery?: string) => void;
  onSelectGuided: (flowType: string) => void;
  onSelectService: (serviceId: string) => void;
  isListening?: boolean;
  onMicClick?: () => void;
}

const GREETINGS: Record<LanguageCode, { title: string; subtitle: string; micLabel: string; searchPlaceholder: string }> = {
  en: {
    title: "Namaskar 👋",
    subtitle: "How can SahkaarSetu help you today?",
    micLabel: "Speak to SahkaarSetu",
    searchPlaceholder: "Type your question about PACS, PMFBY, laws, or schemes…",
  },
  hi: {
    title: "नमस्कार 👋",
    subtitle: "आज सहकारसेतु आपकी क्या सहायता कर सकता है?",
    micLabel: "सहकारसेतु से बोलकर बात करें",
    searchPlaceholder: "पैक्स, फसल बीमा, कानून या योजनाओं के बारे में प्रश्न लिखें…",
  },
  mr: {
    title: "नमस्कार 👋",
    subtitle: "आज सहकारसेतू तुम्हाला कशी मदत करू शकते?",
    micLabel: "सहकारसेतूला बोलून सांगा",
    searchPlaceholder: "पॅक्स, पीक विमा, कायदे किंवा योजनेबाबत प्रश्न विचारा…",
  },
};

const GUIDED_CARDS: Array<{
  id: string;
  icon: string;
  en: string;
  hi: string;
  mr: string;
  descEn: string;
  descHi: string;
  descMr: string;
}> = [
  {
    id: "crop_damage",
    icon: "🌾",
    en: "My crop was damaged",
    hi: "मेरी फसल का नुकसान हुआ है",
    mr: "माझ्या पिकाचे नुकसान झाले आहे",
    descEn: "Step-by-step PMFBY crop insurance & relief guidance",
    descHi: "पीएमएफबीवाई फसल बीमा और मुआवजा सहायता",
    descMr: "PMFBY पीक विमा व मदत मार्गदर्शन",
  },
  {
    id: "pacs_help",
    icon: "🏛️",
    en: "I need help with my PACS",
    hi: "मुझे पैक्स (PACS) सेवा चाहिए",
    mr: "मला पॅक्स (PACS) संदर्भात मदत हवी आहे",
    descEn: "Credit, banking, seeds, and fertilizer services",
    descHi: "ऋण, बैंकिंग, बीज एवं खाद सेवाएं",
    descMr: "कर्ज, बँकिंग, बियाणे व खते सेवा",
  },
  {
    id: "coop_rule",
    icon: "📜",
    en: "I want to understand a cooperative rule",
    hi: "सहकारी नियम और उपविधी समझें",
    mr: "मला सहकारी संस्था नियम समजून घ्यायचा आहे",
    descEn: "Maharashtra Cooperative Societies Act & standard by-laws",
    descHi: "महाराष्ट्र सहकारी अधिनियम और मानक उपनियम",
    descMr: "महाराष्ट्र सहकारी संस्था कायदा व उपविधी",
  },
  {
    id: "financial_guidance",
    icon: "🏦",
    en: "I need financial guidance",
    hi: "मुझे वित्तीय मार्गदर्शन चाहिए",
    mr: "मला आर्थिक मार्गदर्शन हवे आहे",
    descEn: "KCC loans, interest subvention, and savings guidance",
    descHi: "केसीसी ऋण, ब्याज छूट एवं बचत मार्गदर्शन",
    descMr: "KCC कर्ज, व्याज सवलत व बचत मार्गदर्शन",
  },
  {
    id: "grievance_entry",
    icon: "📋",
    en: "I have a cooperative grievance",
    hi: "मुझे शिकायत दर्ज करानी है",
    mr: "मला तक्रार नोंदवायची आहे",
    descEn: "Structured complaint summary builder & official steps",
    descHi: "संरचित शिकायत सारांश और निवारण प्रक्रिया",
    descMr: "रचनात्मक तक्रार सारांश व निवारण पायऱ्या",
  },
  {
    id: "schemes_entry",
    icon: "🏛️",
    en: "I want to know about government schemes",
    hi: "सरकारी योजनाओं की जानकारी पाएं",
    mr: "मला सरकारी योजनांबाबत माहिती हवी आहे",
    descEn: "Computerization of PACS, storage schemes, subsidies",
    descHi: "पैक्स संगणकीकरण, भंडारण योजनाएं एवं सब्सिडी",
    descMr: "PACS संगणकीकरण, गोदाम योजना व सबसिडी",
  },
];

const AssistanceHub: React.FC<Props> = ({
  language,
  onStartAsk,
  onSelectGuided,
  isListening = false,
  onMicClick,
}) => {
  const [textInput, setTextInput] = useState("");
  const locale = GREETINGS[language];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      onStartAsk(textInput.trim());
    }
  };

  return (
    <div className="assistance-hub" aria-label="SahkaarSetu Assistance Hub">
      {/* Hero Welcome Block */}
      <section className="hub-hero">
        <div className="hub-hero__header">
          <h2 className="hub-hero__title">{locale.title}</h2>
          <p className="hub-hero__subtitle">{locale.subtitle}</p>
          <span className="hub-hero__tagline">
            {language === "hi"
              ? "आपका सहकारी साथी"
              : language === "mr"
              ? "तुमचा सहकारी साथी"
              : "Your Cooperative Companion"}
          </span>
        </div>

        {/* Primary Interaction Controls */}
        <div className="hub-hero__actions">
          {/* Prominent Voice CTA */}
          <button
            type="button"
            className={`mic-cta-btn ${isListening ? "mic-cta-btn--listening" : ""}`}
            onClick={onMicClick ?? (() => onStartAsk())}
            aria-label={locale.micLabel}
          >
            <div className="mic-cta-btn__icon">
              <MicIcon size={24} color={isListening ? "#B94A48" : "#176B5B"} />
            </div>
            <div className="mic-cta-btn__text">
              <span className="mic-cta-btn__label">
                {isListening ? "Listening… Speak now" : locale.micLabel}
              </span>
              <span className="mic-cta-btn__sub">
                {isListening ? "Tap to stop" : "Hindi • Marathi • English"}
              </span>
            </div>
          </button>

          {/* Quick Search Input */}
          <form className="hub-search-form" onSubmit={handleSubmit}>
            <input
              type="text"
              className="hub-search-input"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder={locale.searchPlaceholder}
            />
            <button
              type="submit"
              className="hub-search-btn"
              disabled={!textInput.trim()}
              aria-label="Ask SahkaarSetu"
            >
              <SendIcon size={18} color="#FFFFFF" />
            </button>
          </form>
        </div>
      </section>

      {/* Guided Assistance Section */}
      <section className="hub-guided-section">
        <div className="section-header">
          <h3 className="section-title">
            {language === "hi"
              ? "या आपको किस विषय में सहायता चाहिए?"
              : language === "mr"
              ? "किंवा तुम्हाला कशात मदत हवी आहे ते निवडा"
              : "Or choose what you need help with"}
          </h3>
          <p className="section-desc">
            {language === "hi"
              ? "मार्गदर्शित चरणों के साथ त्वरित समाधान प्राप्त करें"
              : language === "mr"
              ? "मार्गदर्शित पायऱ्यांसह त्वरित उपाय मिळवा"
              : "Step-by-step guided flows tailored for rural & cooperative stakeholders"}
          </p>
        </div>

        <div className="guided-cards-grid" role="list">
          {GUIDED_CARDS.map((card) => {
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
                className="guided-card"
                role="listitem"
                onClick={() => onSelectGuided(card.id)}
              >
                <div className="guided-card__icon" aria-hidden="true">
                  {card.icon}
                </div>
                <div className="guided-card__content">
                  <span className="guided-card__title">{title}</span>
                  <span className="guided-card__desc">{desc}</span>
                </div>
                <span className="guided-card__arrow" aria-hidden="true">
                  →
                </span>
              </button>
            );
          })}
        </div>
      </section>
    </div>
  );
};

export default AssistanceHub;
