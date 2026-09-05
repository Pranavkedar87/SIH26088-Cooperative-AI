import React, { useState } from "react";
import type { LanguageCode } from "../types";
import {
  PacsIcon,
  PmfbyIcon,
  LawIcon,
  BylawsIcon,
  FinanceIcon,
} from "./Icons";

interface Props {
  language: LanguageCode;
  onAskAI: (prompt: string) => void;
}

type DomainTab = "pacs" | "pmfby" | "laws" | "bylaws" | "finance";

const DOMAIN_SECTIONS: Record<
  DomainTab,
  {
    icon: React.FC<{ size?: number; color?: string }>;
    titleEn: string;
    titleHi: string;
    titleMr: string;
    subEn: string;
    subHi: string;
    subMr: string;
    topics: Array<{ en: string; hi: string; mr: string; promptEn: string }>;
  }
> = {
  pacs: {
    icon: PacsIcon,
    titleEn: "PACS Services Hub",
    titleHi: "पैक्स (PACS) सेवा केंद्र",
    titleMr: "PACS सेवा केंद्र",
    subEn: "Primary Agricultural Credit Societies credit, fertilizer, and warehouse services",
    subHi: "प्राथमिक कृषि ऋण समितियां - ऋण, उर्वरक और गोदाम सुविधाएं",
    subMr: "प्राथमिक कृषी पतसंस्था - कर्ज, खते व गोदाम सेवा",
    topics: [
      {
        en: "Kisan Credit Card (KCC) short-term crop loans",
        hi: "किसान क्रेडिट कार्ड (केसीसी) फसल ऋण",
        mr: "किसान क्रेडिट कार्ड (KCC) पीक कर्ज",
        promptEn: "How do farmers get KCC crop loans through PACS?",
      },
      {
        en: "Seeds, fertilizer & pesticide distribution at PACS",
        hi: "पैक्स में बीज, खाद और कीटनाशक वितरण",
        mr: "PACS मध्ये बियाणे, खते व कीटकनाशक वितरण",
        promptEn: "What agricultural inputs and fertilizers are distributed at PACS?",
      },
      {
        en: "Warehouse & grain storage scheme at PACS level",
        hi: "पैक्स स्तर पर अनाज भंडारण योजना",
        mr: "PACS पातळीवर धान्य साठवणूक योजना",
        promptEn: "Explain the grain storage facilities and warehouse receipt loans at PACS.",
      },
      {
        en: "PACS Common Service Centers (CSC) digital services",
        hi: "सामान्य सेवा केंद्र (CSC) के रूप में पैक्स सेवाएं",
        mr: "सीएससी (CSC) द्वारे PACS कडून मिळणाऱ्या डिजिटल सेवा",
        promptEn: "What digital and citizen services can be accessed at PACS CSC centers?",
      },
    ],
  },
  pmfby: {
    icon: PmfbyIcon,
    titleEn: "PMFBY Crop Insurance Hub",
    titleHi: "पीएमएफबीवाई फसल बीमा केंद्र",
    titleMr: "PMFBY पीक विमा केंद्र",
    subEn: "Pradhan Mantri Fasal Bima Yojana coverage, claims, and loss assessment",
    subHi: "प्रधानमंत्री फसल बीमा योजना कवरेज, दावा एवं क्षति आकलन",
    subMr: "प्रधानमंत्री पीक विमा योजना संरक्षण, दावे व नुकसान भरपाई",
    topics: [
      {
        en: "72-hour crop damage reporting procedure",
        hi: "फसल नुकसान की 72 घंटे की रिपोर्टिंग प्रक्रिया",
        mr: "७२ तासांच्या आत पीक नुकसानीची माहिती देण्याची प्रक्रिया",
        promptEn: "How do I report crop damage within 72 hours under PMFBY?",
      },
      {
        en: "Post-harvest & localized calamity coverage details",
        hi: "कटाई के बाद और स्थानीय आपदा कवरेज विवरण",
        mr: "कापणीनंतरचे नुकसान व स्थानिक आपत्ती विमा संरक्षण",
        promptEn: "What post-harvest and localized losses are covered under PMFBY?",
      },
      {
        en: "Premium rates for Kharif, Rabi & commercial crops",
        hi: "खरीफ, रबी और व्यावसायिक फसलों की प्रीमियम दरें",
        mr: "खरीप, रब्बी व रोख पिकांचे विमा हप्ते दर",
        promptEn: "What are the farmer premium rates for Kharif and Rabi crops in PMFBY?",
      },
      {
        en: "Required documents for crop insurance claims",
        hi: "फसल बीमा दावों के लिए आवश्यक दस्तावेज",
        mr: "पीक विमा दाव्यासाठी लागणारी आवश्यक कागदपत्रे",
        promptEn: "What documents are required to claim PMFBY crop damage insurance?",
      },
    ],
  },
  laws: {
    icon: LawIcon,
    titleEn: "Maharashtra Cooperative Laws Hub",
    titleHi: "महाराष्ट्र सहकारी कानून केंद्र",
    titleMr: "महाराष्ट्र सहकारी संस्था कायदा केंद्र",
    subEn: "Maharashtra Cooperative Societies Act provisions, voting rights, and legal governance",
    subHi: "महाराष्ट्र सहकारी समिति अधिनियम प्रावधान, मतदान अधिकार एवं कानून",
    subMr: "महाराष्ट्र सहकारी संस्था कायद्यातील तरतुदी, मतदान अधिकार व कायदेशीर नियम",
    topics: [
      {
        en: "Member voting rights & disqualification rules (Sec 26 & 27)",
        hi: "सदस्य मतदान अधिकार और अयोग्यता नियम (धारा 26 एवं 27)",
        mr: "सभासद मतदान अधिकार व अपात्रता नियम (कलम २६ व २७)",
        promptEn: "What are the voting rights and disqualification rules under Sec 26 and 27 of MCS Act?",
      },
      {
        en: "Managing Committee election process & reservations",
        hi: "प्रबंध समिति चुनाव प्रक्रिया एवं आरक्षण",
        mr: "संचालक मंडळ निवडणूक प्रक्रिया व आरक्षण",
        promptEn: "Explain the election rules and committee seat reservations in cooperative societies.",
      },
      {
        en: "Annual General Body Meeting (AGM) requirements & deadlines",
        hi: "वार्षिक साधारण सभा (एजीएम) आवश्यकताएं और समय सीमा",
        mr: "वार्षिक सर्वसाधारण सभा (AGM) नियम व मुदत",
        promptEn: "What are the legal requirements and penalty for delay in conducting AGM?",
      },
      {
        en: "Society audit rules & Financial Year requirements",
        hi: "समिति ऑडिट नियम और वित्तीय वर्ष आवश्यकताएं",
        mr: "संस्थेचे ऑडिट नियम व आर्थिक वर्ष तरतुदी",
        promptEn: "What are the mandatory audit rules and penal consequences for cooperative societies?",
      },
    ],
  },
  bylaws: {
    icon: BylawsIcon,
    titleEn: "Standard Cooperative By-laws",
    titleHi: "मानक सहकारी उप-नियम",
    titleMr: "मानक सहकारी उपविधी",
    subEn: "Model by-laws governing internal rules, member duties, and committee powers",
    subHi: "आंतरिक नियमों, सदस्य कर्तव्यों एवं समिति शक्तियों के उपनियम",
    subMr: "अंतर्गत नियम, सभासद कर्तव्ये व व्यवस्थापक हक्क दर्शवणारी उपविधी",
    topics: [
      {
        en: "Standard membership types (Active, Associate, Nominal)",
        hi: "मानक सदस्यता प्रकार (सक्रिय, सहयोगी, नाममात्र)",
        mr: "सभासदांचे प्रकार (सक्रिय, सहयोगी, नाममात्र)",
        promptEn: "Explain the types of members and rights under standard cooperative by-laws.",
      },
      {
        en: "Procedure for transfer of shares & property rights",
        hi: "शेयर हस्तांतरण और संपत्ति अधिकारों की प्रक्रिया",
        mr: "भाग (शेअर) हस्तांतरण व हक्क हस्तांतरण प्रक्रिया",
        promptEn: "How are share certificates transferred under cooperative society by-laws?",
      },
      {
        en: "Nomination of legal heir procedure",
        hi: "कानूनी वारिस नामांकन प्रक्रिया",
        mr: "कायदेशीर वारस नामनिर्देशन (Nomination) प्रक्रिया",
        promptEn: "What is the legal heir nomination procedure under cooperative by-laws?",
      },
      {
        en: "No-confidence motion against Committee office bearers",
        hi: "समिति पदाधिकारियों के खिलाफ अविश्वास प्रस्ताव",
        mr: "अध्यक्षांविरुद्ध अविश्वास ठराव प्रक्रिया",
        promptEn: "How is a no-confidence motion moved against cooperative committee office bearers?",
      },
    ],
  },
  finance: {
    icon: FinanceIcon,
    titleEn: "Financial Literacy Hub",
    titleHi: "वित्तीय साक्षरता केंद्र",
    titleMr: "आर्थिक साक्षरता केंद्र",
    subEn: "Rural financial planning, credit score discipline, and interest subvention benefits",
    subHi: "ग्रामीण वित्तीय नियोजन, क्रेडिट स्कोर और ब्याज अनुदान लाभ",
    subMr: "ग्रामीण आर्थिक नियोजन, सिबिल स्कोर व व्याज सवलतीचे फायदे",
    topics: [
      {
        en: "3% Interest Subvention for timely KCC repayment",
        hi: "समय पर केसीसी भुगतान पर 3% ब्याज छूट योजना",
        mr: "वेळेवर KCC परतफेडीवर ३% व्याज सवलत योजना",
        promptEn: "How does timely KCC repayment earn 3% interest subvention benefits?",
      },
      {
        en: "Understanding credit score & avoiding default penalties",
        hi: "क्रेडिट स्कोर समझना और डिफॉल्ट से बचना",
        mr: "सिबिल स्कोर समजून घेणे व थकबाकी टाळणे",
        promptEn: "How does cooperative loan default affect CIBIL score and future credit?",
      },
      {
        en: "Deposit Insurance & Credit Guarantee Corporation (DICGC) safety",
        hi: "सहकारी बैंक जमा सुरक्षा योजना (DICGC)",
        mr: "सहकारी बँक ठेवींची सुरक्षितता (DICGC नियम)",
        promptEn: "Are cooperative bank fixed deposits insured up to Rs. 5 Lakhs under DICGC?",
      },
    ],
  },
};

const ServicesDirectory: React.FC<Props> = ({ language, onAskAI }) => {
  const [activeTab, setActiveTab] = useState<DomainTab>("pacs");
  const current = DOMAIN_SECTIONS[activeTab];

  const title = language === "hi" ? current.titleHi : language === "mr" ? current.titleMr : current.titleEn;
  const sub = language === "hi" ? current.subHi : language === "mr" ? current.subMr : current.subEn;

  return (
    <div className="services-directory" aria-label="Cooperative Services Directory">
      {/* Domain Navigation Header Tabs */}
      <div className="services-nav-tabs">
        {(["pacs", "pmfby", "laws", "bylaws", "finance"] as DomainTab[]).map((tab) => {
          const cfg = DOMAIN_SECTIONS[tab];
          const IconComp = cfg.icon;
          const label = language === "hi" ? cfg.titleHi : language === "mr" ? cfg.titleMr : cfg.titleEn;
          const isActive = activeTab === tab;

          return (
            <button
              key={tab}
              type="button"
              className={`service-nav-btn ${isActive ? "service-nav-btn--active" : ""}`}
              onClick={() => setActiveTab(tab)}
            >
              <IconComp size={18} color={isActive ? "#176B5B" : "#64757A"} />
              <span>{label}</span>
            </button>
          );
        })}
      </div>

      {/* Active Domain Panel */}
      <div className="services-panel">
        <div className="services-panel__header">
          <div className="services-panel__title-group">
            <h3 className="services-panel__title">{title}</h3>
            <p className="services-panel__sub">{sub}</p>
          </div>
        </div>

        <div className="services-topics-list">
          {current.topics.map((t, idx) => {
            const topicLabel = language === "hi" ? t.hi : language === "mr" ? t.mr : t.en;

            return (
              <div key={idx} className="topic-card">
                <span className="topic-card__bullet">●</span>
                <span className="topic-card__label">{topicLabel}</span>
                <button
                  type="button"
                  className="topic-card__btn"
                  onClick={() => onAskAI(t.promptEn)}
                >
                  {language === "hi" ? "पूछें" : language === "mr" ? "विचारा" : "Ask AI"} →
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ServicesDirectory;
