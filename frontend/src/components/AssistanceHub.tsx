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
    headline: "सहकारी संस्था व शेतकरी सहाय्यता केंद्र",
    sub: "पीक विमा, पॅक्स कर्ज, कायदेशीर सल्ला आणि योजनांची अधिकृत माहिती मिळवा.",
    voiceBtn: "व्हॉईस सहाय्यक सुरू करा",
    typeOr: "किंवा थेट प्रश्न विचारू शकता:",
    placeholder: "उदा. पीएमएफबीवाय नुकसान भरपाई, पॅक्स पीक कर्ज, ट्रॅक्टर अनुदान...",
    helpHeader: "सहकारी सेवा व योजना विभाग",
    helpSub: "खालीलपैकी योग्य विभाग निवडून अधिकृत माहिती व टप्पा-निहाय मार्गदर्शन मिळवा.",
  },
  hi: {
    headline: "सहकारी संस्था एवं किसान सहायता केंद्र",
    sub: "फसल बीमा, पैक्स ऋण, कानूनी सलाह और सरकारी योजनाओं की आधिकारिक जानकारी प्राप्त करें।",
    voiceBtn: "वॉइस सहायक शुरू करें",
    typeOr: "या सीधे प्रश्न पूछें:",
    placeholder: "उदा. पीएमएफबीवाई फसल नुकसान, पैक्स ऋण प्रक्रिया, ट्रैक्टर सब्सिडी...",
    helpHeader: "सहकारी सेवा एवं योजना प्रभाग",
    helpSub: "आवश्यक विभाग का चयन कर आधिकारिक जानकारी और मार्गदर्शन प्राप्त करें।",
  },
  en: {
    headline: "Cooperative & Agricultural Assistance Portal",
    sub: "Access verified guidance on PMFBY crop insurance, PACS services, credit schemes, and cooperative governance.",
    voiceBtn: "Start Voice Assistant",
    typeOr: "or type your question below:",
    placeholder: "e.g. PMFBY crop loss claim, PACS KCC loan, tractor subsidy...",
    helpHeader: "Cooperative Service & Information Directory",
    helpSub: "Select a core service area to explore verified procedures and document checklists.",
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
    en: "Crop Insurance (PMFBY)",
    hi: "फसल बीमा (PMFBY)",
    mr: "पीक विमा योजना (PMFBY)",
    descEn: "Loss reporting guidelines, timelines, and claim submission",
    descHi: "नुकसान रिपोर्टिंग, समय सीमा और दावा प्रक्रिया",
    descMr: "नुकसान नोंदणी, मुदत आणि भरपाई कार्यपद्धती",
  },
  {
    id: "pacs_help",
    icon: LandmarkIcon,
    en: "PACS Services & Credit",
    hi: "पैक्स सेवाएं एवं ऋण",
    mr: "पॅक्स सेवा व पीक कर्ज",
    descEn: "KCC short-term crop loans, inputs, and membership rules",
    descHi: "केसीसी अल्पकालिक ऋण, उर्वरक और सदस्यता नियम",
    descMr: "अल्पमुदत पीक कर्ज, खते, बियाणे व सभासदत्व",
  },
  {
    id: "coop_rule",
    icon: ScaleIcon,
    en: "Cooperative Law & By-Laws",
    hi: "सहकारी कानून एवं उपनियम",
    mr: "सहकारी कायदा व उपविधी",
    descEn: "MCS Act 1960 provisions, member rights, and audit rules",
    descHi: "एमसीएस अधिनियम 1960, सदस्य अधिकार एवं ऑडिट नियम",
    descMr: "महाराष्ट्र सहकारी संस्था कायदा १९६० व सभासद अधिकार",
  },
  {
    id: "financial_guidance",
    icon: WalletCardsIcon,
    en: "Agricultural Credit & Finance",
    hi: "कृषि ऋण एवं वित्तीय साक्षरता",
    mr: "कृषी पतपुरवठा व वित्तीय नियोजन",
    descEn: "Interest subvention benefits, repayment, and credit scores",
    descHi: "ब्याज अनुदान लाभ, समय पर पुनर्भुगतान और वित्तीय प्रबंधन",
    descMr: "व्याज सवलत, वेळेवर परतफेड व आर्थिक साक्षरता",
  },
  {
    id: "schemes_entry",
    icon: FileCheckIcon,
    en: "Government Welfare Schemes",
    hi: "सरकारी कल्याणकारी योजनाएं",
    mr: "शासकीय कल्याणकारी योजना",
    descEn: "Machinery subsidies, SMAM, storage, and ministry programs",
    descHi: "कृषि यंत्रीकरण (SMAM), भंडारण और मंत्रालय की योजनाएं",
    descMr: "महाडीबीटी कृषी यांत्रिकीकरण व अवजारे अनुदान योजना",
  },
  {
    id: "grievance_entry",
    icon: ClipboardCheckIcon,
    en: "Grievance Redressal",
    hi: "शिकायत निवारण प्रक्रिया",
    mr: "तक्रार निवारण व मदत",
    descEn: "Filing formal complaints with District Deputy Registrar (DDR)",
    descHi: "जिला उप-निबंधक (DDR) के पास औपचारिक शिकायत दर्ज करने की विधि",
    descMr: "जिल्हा उपनिबंधक (DDR) यांच्याकडे तक्रार करण्याची अधिकृत पद्धत",
  },
];

export const AssistanceHub: React.FC<Props> = ({
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
    <div className="assistance-hub" aria-label="Cooperative Assistance Portal Hub">
      {/* Institutional Banner Section */}
      <section className="hub-hero">
        <div className="hub-hero__content">
          <div className="hub-hero__badge">
            <ShieldCheckIcon size={14} color="#123B5D" />
            <span>Ministry of Cooperation Framework Guidance</span>
          </div>
          <h2 className="hub-hero__headline">{t.headline}</h2>
          <p className="hub-hero__sub">{t.sub}</p>

          <div className="hub-action-row">
            {/* Primary Voice Action Button */}
            <button
              type="button"
              className="hero-voice-cta"
              onClick={onOpenVoiceMode}
              aria-label="Start Voice Assistant"
            >
              <MicIcon size={18} color="#FFFFFF" />
              <span className="cta-main-label">{t.voiceBtn}</span>
            </button>

            {/* Direct Search Form */}
            <form onSubmit={handleTextSubmit} className="hero-search-form" role="search">
              <input
                type="text"
                className="hero-search-input"
                value={typedInput}
                onChange={(e) => setTypedInput(e.target.value)}
                placeholder={t.placeholder}
                aria-label="Search cooperative guidance topic"
              />
              <button
                type="submit"
                className="hero-search-submit"
                disabled={!typedInput.trim()}
                aria-label="Submit Question"
              >
                <SendIcon size={15} color="#FFFFFF" />
              </button>
            </form>
          </div>
        </div>
      </section>

      {/* Structured Service Directory Section */}
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
                  <IconComp size={18} color="#123B5D" />
                </div>
                <div className="hub-service-card__body">
                  <span className="hub-service-card__title">{title}</span>
                  <span className="hub-service-card__desc">{desc}</span>
                </div>
                <div className="hub-service-card__arrow">
                  <ArrowRightIcon size={14} color="#4A5D6E" />
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* Institutional Trust & Reference Footer */}
      <footer className="hub-trust-footer">
        <div className="trust-item">
          <ShieldCheckIcon size={13} color="#0F6B68" />
          <span>Verified Government & NABARD Information Sources</span>
        </div>
        <span className="trust-dot">•</span>
        <div className="trust-item">
          <span>Multilingual Assistance (Hindi • Marathi • English)</span>
        </div>
      </footer>
    </div>
  );
};

export default AssistanceHub;
