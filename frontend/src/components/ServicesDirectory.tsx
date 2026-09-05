import React, { useState } from "react";
import type { LanguageCode } from "../types";
import {
  LandmarkIcon,
  WheatIcon,
  ScaleIcon,
  FileTextIcon,
  WalletCardsIcon,
  FileCheckIcon,
  ClipboardCheckIcon,
  ArrowRightIcon,
} from "./Icons";

interface Props {
  language: LanguageCode;
  onAskAI: (prompt: string) => void;
}

type DomainTab = "pacs" | "pmfby" | "laws" | "bylaws" | "finance" | "schemes" | "grievance";

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
    icon: LandmarkIcon,
    titleEn: "PACS Services",
    titleHi: "पैक्स (PACS) सेवाएं",
    titleMr: "PACS सेवा",
    subEn: "Primary Agricultural Credit Societies credit, fertilizer, seeds, and warehouse services",
    subHi: "प्राथमिक कृषि ऋण समितियां - ऋण, उर्वरक, बीज और भंडारण सेवाएं",
    subMr: "प्राथमिक कृषी पतसंस्था - कर्ज, खते, बियाणे व गोदाम सेवा",
    topics: [
      {
        en: "Kisan Credit Card (KCC) short-term crop loans & subvention",
        hi: "किसान क्रेडिट कार्ड (केसीसी) फसल ऋण और ब्याज छूट",
        mr: "किसान क्रेडिट कार्ड (KCC) पीक कर्ज व व्याज सवलत",
        promptEn: "How do farmers get KCC crop loans through PACS?",
      },
      {
        en: "Seeds, fertilizer & pesticide distribution at PACS",
        hi: "पैक्स में बीज, खाद और कीटनाशक वितरण",
        mr: "PACS मध्ये बियाणे, खते व कीटकनाशक वितरण",
        promptEn: "What agricultural inputs and fertilizers are distributed at PACS?",
      },
      {
        en: "Warehouse & grain storage receipt loans at PACS level",
        hi: "पैक्स स्तर पर अनाज भंडारण एवं रसीद ऋण योजना",
        mr: "PACS पातळीवर धान्य साठवणूक व पावती कर्ज योजना",
        promptEn: "Explain the grain storage facilities and warehouse receipt loans at PACS.",
      },
      {
        en: "PACS Common Service Centers (CSC) digital citizen services",
        hi: "सामान्य सेवा केंद्र (CSC) के रूप में पैक्स सेवाएं",
        mr: "सीएससी (CSC) द्वारे PACS कडून मिळणाऱ्या डिजिटल सेवा",
        promptEn: "What digital and citizen services can be accessed at PACS CSC centers?",
      },
    ],
  },
  pmfby: {
    icon: WheatIcon,
    titleEn: "Crop & Insurance (PMFBY)",
    titleHi: "फसल और बीमा (पीएमएफबीवाई)",
    titleMr: "पीक आणि विमा (PMFBY)",
    subEn: "Pradhan Mantri Fasal Bima Yojana coverage, 72-hour claim steps, and damage relief",
    subHi: "प्रधानमंत्री फसल बीमा योजना कवरेज, 72 घंटे की दावा प्रक्रिया और सहायता",
    subMr: "प्रधानमंत्री पीक विमा योजना संरक्षण, ७२ तासांत दावा व नुकसान भरपाई",
    topics: [
      {
        en: "72-hour crop damage intimating procedure",
        hi: "फसल नुकसान की 72 घंटे की सूचना प्रक्रिया",
        mr: "७२ तासांच्या आत पीक नुकसानीची माहिती देण्याची प्रक्रिया",
        promptEn: "How do I report crop damage within 72 hours under PMFBY?",
      },
      {
        en: "Post-harvest & localized inundation calamity coverage",
        hi: "कटाई के बाद और स्थानीय जलभराव आपदा कवरेज",
        mr: "कापणीनंतरचे नुकसान व स्थानिक आपत्ती विमा संरक्षण",
        promptEn: "What post-harvest and localized losses are covered under PMFBY?",
      },
      {
        en: "Premium rates for Kharif, Rabi & commercial crops",
        hi: "खरीफ, रबी और व्यावसायिक फसलों की प्रीमियम दरें",
        mr: "खरीप, रब्बी व रोख पिकांचे विमा हप्ते दर",
        promptEn: "What are the farmer premium rates for Kharif and Rabi crops in PMFBY?",
      },
    ],
  },
  laws: {
    icon: ScaleIcon,
    titleEn: "Cooperative Laws",
    titleHi: "सहकारी कानून",
    titleMr: "सहकारी कायदे",
    subEn: "Maharashtra Cooperative Societies Act provisions, voting rights, and audit rules",
    subHi: "महाराष्ट्र सहकारी समिति अधिनियम प्रावधान, मतदान अधिकार एवं ऑडिट नियम",
    subMr: "महाराष्ट्र सहकारी संस्था कायद्यातील तरतुदी, मतदान अधिकार व ऑडिट नियम",
    topics: [
      {
        en: "Member voting rights & disqualification rules (Sec 26 & 27)",
        hi: "सदस्य मतदान अधिकार और अयोग्यता नियम (धारा 26 एवं 27)",
        mr: "सभासद मतदान अधिकार व अपात्रता नियम (कलम २६ व २७)",
        promptEn: "What are the voting rights and disqualification rules under Sec 26 and 27 of MCS Act?",
      },
      {
        en: "Managing Committee election rules & tenure limits",
        hi: "प्रबंध समिति चुनाव नियम एवं कार्यकाल सीमा",
        mr: "संचालक मंडळ निवडणूक नियम व मुदत मर्यादा",
        promptEn: "Explain the election rules and committee tenure in cooperative societies.",
      },
      {
        en: "Annual General Meeting (AGM) deadlines & legal consequences",
        hi: "वार्षिक साधारण सभा (एजीएम) की समय सीमा और कानूनी परिणाम",
        mr: "वार्षिक सर्वसाधारण सभा (AGM) मुदत व कायदेशीर तरतुदी",
        promptEn: "What are the legal requirements and penalty for delay in conducting AGM?",
      },
    ],
  },
  bylaws: {
    icon: FileTextIcon,
    titleEn: "Cooperative By-laws",
    titleHi: "सहकारी उप-नियम",
    titleMr: "सहकारी उपविधी",
    subEn: "Model by-laws governing internal rules, member classes, and share transfer",
    subHi: "आंतरिक नियमों, सदस्य श्रेणियों और शेयर हस्तांतरण के उपनियम",
    subMr: "अंतर्गत नियम, सभासद वर्ग व भाग हस्तांतरण दर्शवणारी उपविधी",
    topics: [
      {
        en: "Standard membership types (Active, Associate, Nominal)",
        hi: "मानक सदस्यता प्रकार (सक्रिय, सहयोगी, नाममात्र)",
        mr: "सभासदांचे प्रकार (सक्रिय, सहयोगी, नाममात्र)",
        promptEn: "Explain the types of members and rights under standard cooperative by-laws.",
      },
      {
        en: "Procedure for transfer of share certificates & property rights",
        hi: "शेयर प्रमाण पत्र और संपत्ति अधिकारों के हस्तांतरण की प्रक्रिया",
        mr: "भाग (शेअर) प्रमाणपत्र व हक्क हस्तांतरण प्रक्रिया",
        promptEn: "How are share certificates transferred under cooperative society by-laws?",
      },
      {
        en: "Nomination of legal heir procedure",
        hi: "कानूनी वारिस नामांकन प्रक्रिया",
        mr: "कायदेशीर वारस नामनिर्देशन (Nomination) प्रक्रिया",
        promptEn: "What is the legal heir nomination procedure under cooperative by-laws?",
      },
    ],
  },
  finance: {
    icon: WalletCardsIcon,
    titleEn: "Financial Literacy",
    titleHi: "वित्तीय साक्षरता",
    titleMr: "आर्थिक साक्षरता",
    subEn: "Rural financial discipline, interest subvention benefits, and deposit safety",
    subHi: "ग्रामीण वित्तीय अनुशासन, ब्याज अनुदान लाभ और जमा सुरक्षा",
    subMr: "ग्रामीण आर्थिक शिस्त, व्याज सवलत व ठेव सुरक्षा",
    topics: [
      {
        en: "3% Interest Subvention for prompt KCC repayment",
        hi: "समय पर केसीसी भुगतान करने पर 3% ब्याज छूट योजना",
        mr: "वेळेवर KCC परतफेडीवर ३% व्याज सवलत योजना",
        promptEn: "How does timely KCC repayment earn 3% interest subvention benefits?",
      },
      {
        en: "CIBIL credit score impact & default penalties",
        hi: "सिबिल क्रेडिट स्कोर प्रभाव और डिफॉल्ट पेनल्टी",
        mr: "सिबिल स्कोर प्रभाव व थकबाकी टाळणे",
        promptEn: "How does cooperative loan default affect CIBIL score and future credit?",
      },
      {
        en: "Deposit Insurance (DICGC) safety up to Rs. 5 Lakhs",
        hi: "सहकारी बैंक जमा सुरक्षा योजना (DICGC)",
        mr: "सहकारी बँक ठेवींची सुरक्षा (DICGC नियम)",
        promptEn: "Are cooperative bank fixed deposits insured up to Rs. 5 Lakhs under DICGC?",
      },
    ],
  },
  schemes: {
    icon: FileCheckIcon,
    titleEn: "Government Schemes",
    titleHi: "सरकारी योजनाएं",
    titleMr: "सरकारी योजना",
    subEn: "Ministry of Cooperation national schemes, PACS ERP, and storage infrastructure",
    subHi: "सहकार मंत्रालय की राष्ट्रीय योजनाएं, ईआरपी और भंडारण संरचना",
    subMr: "सहकार मंत्रालयाच्या राष्ट्रीय योजना, संगणकीकरण व गोदाम विकास",
    topics: [
      {
        en: "PACS Computerization & ERP integration scheme",
        hi: "पैक्स संगणकीकरण और ईआरपी योजना",
        mr: "PACS संगणकीकरण व प्रणाली योजना",
        promptEn: "Explain the national scheme for PACS Computerization and ERP implementation.",
      },
      {
        en: "World's Largest Grain Storage Plan in Cooperative Sector",
        hi: "सहकारी क्षेत्र में विश्व की सबसे बड़ी अनाज भंडारण योजना",
        mr: "सहकार क्षेत्रातील जगातील सर्वात मोठी धान्य साठवणूक योजना",
        promptEn: "Explain the grain storage plan created for primary agricultural credit societies.",
      },
    ],
  },
  grievance: {
    icon: ClipboardCheckIcon,
    titleEn: "Grievance Assistance",
    titleHi: "शिकायत सहायता",
    titleMr: "तक्रार निवारण",
    subEn: "Structured complaint redressal guidance and Registrar submission procedures",
    subHi: "संरचित शिकायत निवारण मार्गदर्शन और निबंधक प्रस्तुति प्रक्रिया",
    subMr: "रचनात्मक तक्रार निवारण मार्गदर्शक व निबंधक सादरकरण पायऱ्या",
    topics: [
      {
        en: "Procedure to file complaint with District Deputy Registrar (DDR)",
        hi: "जिला उप निबंधक (DDR) के पास शिकायत दर्ज करने की प्रक्रिया",
        mr: "जिल्हा उपनिबंधकांकडे (DDR) तक्रार नोंदवण्याची प्रक्रिया",
        promptEn: "What is the official procedure to file a grievance with District Deputy Registrar (DDR)?",
      },
      {
        en: "Grievance redressal for PACS loan refusal or membership denial",
        hi: "पैक्स ऋण इनकार या सदस्यता इनकार के लिए शिकायत निवारण",
        mr: "PACS कडून कर्ज किंवा सभासदत्व नाकारल्यास तक्रार कशी करावी?",
        promptEn: "How do I file a grievance if PACS denies loan or membership without valid reasons?",
      },
    ],
  },
};

const ServicesDirectory: React.FC<Props> = ({ language, onAskAI }) => {
  const [activeTab, setActiveTab] = useState<DomainTab>("pacs");
  const current = DOMAIN_SECTIONS[activeTab];

  const IconMain = current.icon;
  const title = language === "hi" ? current.titleHi : language === "mr" ? current.titleMr : current.titleEn;
  const sub = language === "hi" ? current.subHi : language === "mr" ? current.subMr : current.subEn;

  return (
    <div className="services-directory" aria-label="Services Directory">
      <div className="services-nav-bar">
        {(["pacs", "pmfby", "laws", "bylaws", "finance", "schemes", "grievance"] as DomainTab[]).map((tab) => {
          const cfg = DOMAIN_SECTIONS[tab];
          const IconTab = cfg.icon;
          const label = language === "hi" ? cfg.titleHi : language === "mr" ? cfg.titleMr : cfg.titleEn;
          const isActive = activeTab === tab;

          return (
            <button
              key={tab}
              type="button"
              className={`services-tab-btn ${isActive ? "services-tab-btn--active" : ""}`}
              onClick={() => setActiveTab(tab)}
            >
              <IconTab size={16} color={isActive ? "#176B5B" : "#66777A"} />
              <span>{label}</span>
            </button>
          );
        })}
      </div>

      <div className="services-panel">
        <div className="services-panel__header">
          <div className="services-panel__icon">
            <IconMain size={24} color="#176B5B" />
          </div>
          <div className="services-panel__titles">
            <h3 className="services-panel__title">{title}</h3>
            <p className="services-panel__sub">{sub}</p>
          </div>
        </div>

        <div className="services-topics-list">
          {current.topics.map((t, idx) => {
            const topicLabel = language === "hi" ? t.hi : language === "mr" ? t.mr : t.en;

            return (
              <div key={idx} className="topic-card">
                <span className="topic-card__label">{topicLabel}</span>
                <button
                  type="button"
                  className="topic-card__btn"
                  onClick={() => onAskAI(t.promptEn)}
                >
                  <span>{language === "hi" ? "पूछें" : language === "mr" ? "विचारा" : "Ask"}</span>
                  <ArrowRightIcon size={14} color="#FFFFFF" />
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
