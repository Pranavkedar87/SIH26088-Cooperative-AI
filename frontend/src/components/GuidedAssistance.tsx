import React, { useState } from "react";
import type { LanguageCode } from "../types";
import {
  WheatIcon,
  LandmarkIcon,
  ScaleIcon,
  WalletCardsIcon,
  FileCheckIcon,
  ArrowRightIcon,
  CheckIcon,
  ShieldCheckIcon,
} from "./Icons";

interface Props {
  flowType: string;
  language: LanguageCode;
  onAskAI: (prompt: string) => void;
  onBack: () => void;
}

interface StepOption {
  id: string;
  en: string;
  hi: string;
  mr: string;
}

interface FlowConfig {
  titleEn: string;
  titleHi: string;
  titleMr: string;
  icon: React.FC<{ size?: number; color?: string }>;
  step1Question: { en: string; hi: string; mr: string };
  step1Options: StepOption[];
  step2Question: { en: string; hi: string; mr: string };
  step2Options: StepOption[];
  checklist: Array<{ en: string; hi: string; mr: string }>;
  promptTemplate: (opt1: string, opt2: string) => string;
}

const FLOW_CONFIGS: Record<string, FlowConfig> = {
  crop_damage: {
    titleEn: "PMFBY Crop & Insurance Guidance",
    titleHi: "पीएमएफबीवाई फसल और बीमा सहायता",
    titleMr: "PMFBY पीक व विमा मार्गदर्शन",
    icon: WheatIcon,
    step1Question: {
      en: "What happened to your crop?",
      hi: "आपकी फसल के साथ क्या हुआ?",
      mr: "पिकाचे कशामुळे नुकसान झाले?",
    },
    step1Options: [
      { id: "rain", en: "Excessive Rain / Inundation", hi: "अत्यधिक वर्षा / जलभराव", mr: "अतिवृष्टी / पूर" },
      { id: "hail", en: "Hailstorm / Cyclone", hi: "ओला वृष्टि / चक्रवात", mr: "गारपीट / वादळ" },
      { id: "drought", en: "Dry Spell / Drought", hi: "सूखा / वर्षा की कमी", mr: "दुष्काळ / पावसाचा खंड" },
      { id: "pest", en: "Pest / Disease Attack", hi: "कीट / रोग का प्रकोप", mr: "कीड / रोग प्रादुर्भाव" },
    ],
    step2Question: {
      en: "What are you trying to understand?",
      hi: "आप क्या जानना चाहते हैं?",
      mr: "तुम्हाला नक्की काय समजून घ्यायचे आहे?",
    },
    step2Options: [
      { id: "claim", en: "72-hour claim reporting steps", hi: "72 घंटे की दावा सूचना प्रक्रिया", mr: "७२ तासांत दावा कळवण्याच्या पायऱ्या" },
      { id: "coverage", en: "Coverage & sum insured", hi: "बीमा कवरेज और बीमित राशि", mr: "विमा संरक्षण व रक्कम" },
      { id: "docs", en: "Required document checklist", hi: "आवश्यक दस्तावेजों की सूची", mr: "लागणारी आवश्यक कागदपत्रे" },
    ],
    checklist: [
      { en: "Notify insurance company within 72 hours of damage", hi: "नुकसान के 72 घंटे के भीतर बीमा कंपनी को सूचित करें", mr: "७२ तासांच्या आत विमा कंपनीस कळवा" },
      { en: "Keep 7/12 land extract & bank passbook copy ready", hi: "7/12 भूमि विवरण एवं बैंक पासबुक रखें", mr: "७/१२ उतारा व बँक पासबुक तयार ठेवा" },
      { en: "Take clear photos of the affected crop field", hi: "प्रभावित फसल क्षेत्र की तस्वीरें लें", mr: "नुकसानग्रस्त पिकाचे स्पष्ट फोटो काढा" },
    ],
    promptTemplate: (opt1, opt2) =>
      `My crop suffered ${opt1}. I want to understand ${opt2} under PMFBY. What are the official steps, required documents, and contact details?`,
  },
  pacs_help: {
    titleEn: "PACS Services Guidance",
    titleHi: "पैक्स (PACS) सेवा मार्गदर्शन",
    titleMr: "PACS सेवा मार्गदर्शन",
    icon: LandmarkIcon,
    step1Question: {
      en: "Which service do you need guidance on?",
      hi: "आपको किस पैक्स सेवा पर मार्गदर्शन चाहिए?",
      mr: "तुम्हाला कोणत्या PACS सेवेबाबत माहिती हवी आहे?",
    },
    step1Options: [
      { id: "loan", en: "KCC Short-Term Crop Loan", hi: "केसीसी अल्पकालिक फसल ऋण", mr: "KCC अल्पमुदत पीक कर्ज" },
      { id: "inputs", en: "Fertilizers & Seeds Purchase", hi: "उर्वरक एवं बीज खरीद", mr: "खते व बियाणे खरेदी" },
      { id: "storage", en: "Warehouse & Grain Storage", hi: "गोदाम एवं अनाज भंडारण", mr: "गोदाम व धान्य साठवणूक" },
      { id: "membership", en: "PACS Membership Application", hi: "पैक्स सदस्यता आवेदन", mr: "PACS सभासदत्व अर्ज" },
    ],
    step2Question: {
      en: "What is your current status?",
      hi: "आपकी वर्तमान स्थिति क्या है?",
      mr: "तुमची सध्याची स्थिती काय आहे?",
    },
    step2Options: [
      { id: "active", en: "Active PACS member", hi: "सक्रिय पैक्स सदस्य", mr: "सक्रिय PACS सभासद" },
      { id: "new", en: "New applicant", hi: "नया आवेदक", mr: "नवीन अर्जदार" },
    ],
    checklist: [
      { en: "Aadhaar Card & PAN Card", hi: "आधार कार्ड एवं पैन कार्ड", mr: "आधार कार्ड व पॅन कार्ड" },
      { en: "7/12 Land ownership Record", hi: "7/12 भूमि स्वामित्व दस्तावेज", mr: "७/१२ जमीन उतारा" },
      { en: "No-dues certificate from local DCCB bank", hi: "स्थानीय डीसीसीबी बैंक से बकाया न होने का प्रमाण पत्र", mr: "DCCB बँकेचे थकबाकी नसल्याचे प्रमाणपत्र" },
    ],
    promptTemplate: (opt1, opt2) =>
      `I am a ${opt2} seeking guidance on ${opt1} at PACS. What is the process, interest rate benefit, and document checklist?`,
  },
  coop_rule: {
    titleEn: "Cooperative Rules & By-laws",
    titleHi: "सहकारी नियम और उपनियम",
    titleMr: "सहकारी नियम व उपविधी",
    icon: ScaleIcon,
    step1Question: {
      en: "Which rule topic do you want to understand?",
      hi: "आप किस नियम विषय को समझना चाहते हैं?",
      mr: "तुम्हाला कोणत्या नियमाबाबत माहिती हवी आहे?",
    },
    step1Options: [
      { id: "rights", en: "Member Voting Rights (Sec 27)", hi: "सदस्य मतदान अधिकार (धारा 27)", mr: "सभासद मतदान अधिकार (कलम २७)" },
      { id: "election", en: "Managing Committee Election", hi: "प्रबंध समिति चुनाव", mr: "संचालक मंडळ निवडणूक" },
      { id: "agm", en: "Annual General Meeting (AGM)", hi: "वार्षिक साधारण सभा (AGM)", mr: "वार्षिक सर्वसाधारण सभा (AGM)" },
    ],
    step2Question: {
      en: "What is your goal?",
      hi: "आपका उद्देश्य क्या है?",
      mr: "तुमचा उद्देश काय आहे?",
    },
    step2Options: [
      { id: "understand", en: "Understand legal provisions", hi: "कानूनी प्रावधान समझना", mr: "कायदेशीर तरतुदी समजून घेणे" },
      { id: "dispute", en: "Address a governance dispute", hi: "प्रबंधन विवाद का निवारण", mr: "व्यवस्थापन वादावर तोडगा" },
    ],
    checklist: [
      { en: "Refer to Maharashtra Cooperative Societies Act 1960", hi: "महाराष्ट्र सहकारी समिति अधिनियम 1960 देखें", mr: "महाराष्ट्र सहकारी संस्था कायदा १९६० पहा" },
      { en: "Check Model By-laws Sections 22 to 35", hi: "मॉडल उपनियम धारा 22 से 35 देखें", mr: "मॉडेल उपविधी कलम २२ ते ३५ तपासा" },
    ],
    promptTemplate: (opt1, opt2) =>
      `Explain the Maharashtra Cooperative Societies Act rules regarding ${opt1} to help ${opt2}.`,
  },
  financial_guidance: {
    titleEn: "Financial Literacy Guidance",
    titleHi: "वित्तीय साक्षरता मार्गदर्शन",
    titleMr: "आर्थिक साक्षरता मार्गदर्शन",
    icon: WalletCardsIcon,
    step1Question: {
      en: "What financial topic do you need help with?",
      hi: "आपको किस वित्तीय विषय पर सहायता चाहिए?",
      mr: "तुम्हाला कोणत्या आर्थिक विषयावर माहिती हवी आहे?",
    },
    step1Options: [
      { id: "subvention", en: "3% Interest Subvention for KCC", hi: "केसीसी पर 3% ब्याज छूट योजना", mr: "KCC वर ३% व्याज सवलत योजना" },
      { id: "credit_score", en: "CIBIL Credit Score & Repayment", hi: "सिबिल क्रेडिट स्कोर और पुनर्भुगतान", mr: "सिबिल क्रेडिट स्कोर व परतफेड" },
      { id: "deposit_safety", en: "Cooperative Bank Deposit Safety (DICGC)", hi: "सहकारी बैंक जमा सुरक्षा (DICGC)", mr: "सहकारी बँक ठेव सुरक्षा (DICGC)" },
    ],
    step2Question: {
      en: "What guidance do you require?",
      hi: "आपको कैसा मार्गदर्शन चाहिए?",
      mr: "तुम्हाला कसे मार्गदर्शन हवे आहे?",
    },
    step2Options: [
      { id: "explain", en: "Simple explanation with example", hi: "उदाहरण के साथ सरल व्याख्या", mr: "उदाहरणासह सोपे स्पष्टीकरण" },
      { id: "action", en: "Actionable steps to apply", hi: "आवेदन के लिए व्यावहारिक कदम", mr: "अर्जासाठी प्रत्यक्ष पायऱ्या" },
    ],
    checklist: [
      { en: "Timely repayment earns 3% prompt repayment incentive", hi: "समय पर भुगतान करने पर 3% प्रोत्साहन छूट मिलती है", mr: "वेळेवर परतफेडीवर ३% सवलत मिळते" },
      { en: "Deposits insured up to Rs. 5 Lakhs per depositor", hi: "प्रति जमाकर्ता 5 लाख रुपये तक जमा बीमा संरक्षित", mr: "प्रत्येक ठेवीदारासाठी ५ लाखांपर्यंत विमा संरक्षण" },
    ],
    promptTemplate: (opt1, opt2) =>
      `Provide financial literacy guidance on ${opt1}. Give a ${opt2} for farmers and cooperative members.`,
  },
  schemes_entry: {
    titleEn: "Government Schemes Guidance",
    titleHi: "सरकारी योजना मार्गदर्शन",
    titleMr: "सरकारी योजना मार्गदर्शन",
    icon: FileCheckIcon,
    step1Question: {
      en: "Which Ministry of Cooperation scheme do you want to explore?",
      hi: "आप किस सहकार मंत्रालय योजना की जानकारी चाहते हैं?",
      mr: "तुम्हाला कोणत्या सहकार मंत्रालय योजनेची माहिती हवी आहे?",
    },
    step1Options: [
      { id: "comp", en: "PACS Computerization & ERP", hi: "पैक्स संगणकीकरण और ईआरपी", mr: "PACS संगणकीकरण व संगणक प्रणाली" },
      { id: "storage", en: "World's Largest Grain Storage Plan", hi: "अन्न भंडारण योजना", mr: "धान्य साठवणूक योजना" },
      { id: "csc", en: "PACS as Common Service Centers", hi: "सामान्य सेवा केंद्र के रूप में पैक्स", mr: "सीएससी (CSC) म्हणून PACS सेवा" },
    ],
    step2Question: {
      en: "What do you want to know?",
      hi: "आप क्या जानना चाहते हैं?",
      mr: "तुम्हाला काय माहिती करून घ्यायचे आहे?",
    },
    step2Options: [
      { id: "benefits", en: "Benefits & Eligibility", hi: "लाभ और पात्रता", mr: "फायदे व पात्रता" },
      { id: "apply", en: "How to participate", hi: "भाग कैसे लें", mr: "सहभाग कसा घ्यावा" },
    ],
    checklist: [
      { en: "Check Central Registrar of Cooperative Societies portal", hi: "केंद्रीय सहकारी समिति निबंधक पोर्टल देखें", mr: "केंद्रीय सहकार निबंधक पोर्टल तपासा" },
      { en: "Contact local District Central Cooperative Bank (DCCB)", hi: "स्थानीय जिला मध्यवर्ती सहकारी बैंक से संपर्क करें", mr: "जिल्हा मध्यवर्ती सहकारी बँकेशी संपर्क साधा" },
    ],
    promptTemplate: (opt1, opt2) =>
      `Explain the government scheme regarding ${opt1}, focusing on ${opt2} for cooperative societies.`,
  },
};

const GuidedAssistance: React.FC<Props> = ({ flowType, language, onAskAI, onBack }) => {
  const config = FLOW_CONFIGS[flowType] ?? FLOW_CONFIGS.crop_damage;

  const [step1Val, setStep1Val] = useState<StepOption | null>(config.step1Options[0] ?? null);
  const [step2Val, setStep2Val] = useState<StepOption | null>(config.step2Options[0] ?? null);
  const [currentStep, setCurrentStep] = useState<number>(1);

  const IconComp = config.icon;
  const title = language === "hi" ? config.titleHi : language === "mr" ? config.titleMr : config.titleEn;
  const q1 = config.step1Question[language] ?? config.step1Question.en;
  const q2 = config.step2Question[language] ?? config.step2Question.en;

  const handleFinish = () => {
    const s1Text = step1Val ? (step1Val[language] ?? step1Val.en) : "";
    const s2Text = step2Val ? (step2Val[language] ?? step2Val.en) : "";
    const prompt = config.promptTemplate(s1Text, s2Text);
    onAskAI(prompt);
  };

  return (
    <div className="guided-wizard" aria-label="Guided Assistance Wizard">
      {/* Wizard Header Bar */}
      <div className="wizard-header">
        <button type="button" className="wizard-back-btn" onClick={onBack} aria-label="Go back">
          ← {language === "hi" ? "वापस" : language === "mr" ? "मागे" : "Back"}
        </button>
        <div className="wizard-title-group">
          <IconComp size={22} color="#176B5B" />
          <h3 className="wizard-title">{title}</h3>
        </div>
      </div>

      {/* Progress Line Bar: 1 ── 2 ── 3 */}
      <div className="wizard-progress">
        <div className={`progress-step ${currentStep >= 1 ? "progress-step--active" : ""}`}>
          <span className="step-num">1</span>
          <span className="step-label">
            {language === "hi" ? "स्थिति" : language === "mr" ? "परिस्थिती" : "Situation"}
          </span>
        </div>
        <div className="progress-line" />
        <div className={`progress-step ${currentStep >= 2 ? "progress-step--active" : ""}`}>
          <span className="step-num">2</span>
          <span className="step-label">
            {language === "hi" ? "आवश्यकता" : language === "mr" ? "गरज" : "Requirement"}
          </span>
        </div>
        <div className="progress-line" />
        <div className={`progress-step ${currentStep >= 3 ? "progress-step--active" : ""}`}>
          <span className="step-num">3</span>
          <span className="step-label">
            {language === "hi" ? "मार्गदर्शन" : language === "mr" ? "मार्गदर्शन" : "Guidance"}
          </span>
        </div>
      </div>

      {/* Step Panels */}
      <div className="wizard-body">
        {currentStep === 1 && (
          <div className="wizard-step-panel">
            <h4 className="step-question">{q1}</h4>
            <div className="step-options">
              {config.step1Options.map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  className={`opt-card ${step1Val?.id === opt.id ? "opt-card--selected" : ""}`}
                  onClick={() => setStep1Val(opt)}
                >
                  <span className="opt-indicator">{step1Val?.id === opt.id ? "●" : "○"}</span>
                  <span className="opt-text">{opt[language] ?? opt.en}</span>
                </button>
              ))}
            </div>
            <button
              type="button"
              className="wizard-next-btn"
              onClick={() => setCurrentStep(2)}
            >
              <span>{language === "hi" ? "आगे बढ़ें" : language === "mr" ? "पुढे जा" : "Next Step"}</span>
              <ArrowRightIcon size={16} color="#FFFFFF" />
            </button>
          </div>
        )}

        {currentStep === 2 && (
          <div className="wizard-step-panel">
            <h4 className="step-question">{q2}</h4>
            <div className="step-options">
              {config.step2Options.map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  className={`opt-card ${step2Val?.id === opt.id ? "opt-card--selected" : ""}`}
                  onClick={() => setStep2Val(opt)}
                >
                  <span className="opt-indicator">{step2Val?.id === opt.id ? "●" : "○"}</span>
                  <span className="opt-text">{opt[language] ?? opt.en}</span>
                </button>
              ))}
            </div>
            <div className="wizard-btn-row">
              <button
                type="button"
                className="wizard-sec-btn"
                onClick={() => setCurrentStep(1)}
              >
                ← {language === "hi" ? "पिछला" : language === "mr" ? "मागे" : "Previous"}
              </button>
              <button
                type="button"
                className="wizard-next-btn"
                onClick={() => setCurrentStep(3)}
              >
                <span>{language === "hi" ? "मार्गदर्शन देखें" : language === "mr" ? "मार्गदर्शन पहा" : "View Guidance"}</span>
                <ArrowRightIcon size={16} color="#FFFFFF" />
              </button>
            </div>
          </div>
        )}

        {currentStep === 3 && (
          <div className="wizard-step-panel">
            <h4 className="step-question">
              {language === "hi"
                ? "आवश्यक चेकलिस्ट एवं कार्रवाई"
                : language === "mr"
                ? "आवश्यक यादी व कारवाई"
                : "Required Checklist & Next Steps"}
            </h4>

            <div className="checklist-box">
              <span className="checklist-title">
                {language === "hi" ? "आवश्यक दस्तावेज एवं कदम" : language === "mr" ? "महत्त्वाची कागदपत्रे व पायऱ्या" : "Document & Action Checklist"}
              </span>
              <ul className="checklist-items">
                {config.checklist.map((item, idx) => (
                  <li key={idx}>
                    <CheckIcon size={14} color="#2F855A" />
                    <span>{item[language] ?? item.en}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="wizard-summary-callout">
              <div className="callout-header">
                <ShieldCheckIcon size={16} color="#176B5B" />
                <span className="callout-heading">
                  {language === "hi" ? "सहकारसेतु प्रामाणिक मार्गदर्शन" : language === "mr" ? "सहकारसेतू अधिकृत मार्गदर्शन" : "SahkaarSetu Source-backed Guidance"}
                </span>
              </div>
              <p className="callout-text">
                {language === "hi"
                  ? "अब आप सहकारसेतु से आधिकारिक ज्ञानकोश पर आधारित उत्तर प्राप्त कर सकते हैं।"
                  : language === "mr"
                  ? "आता तुम्ही सहकारसेतूकडून अधिकृत ज्ञानकोशावर आधारित उत्तर मिळवू शकता."
                  : "Click below to query SahkaarSetu for source-backed rules, claim guidance, and next steps."}
              </p>
            </div>

            <div className="wizard-btn-row">
              <button
                type="button"
                className="wizard-sec-btn"
                onClick={() => setCurrentStep(2)}
              >
                ← {language === "hi" ? "पिछला" : language === "mr" ? "मागे" : "Previous"}
              </button>
              <button type="button" className="wizard-next-btn" onClick={handleFinish}>
                <span>{language === "hi" ? "उत्तर प्राप्त करें" : language === "mr" ? "उत्तर मिळवा" : "Get Source-backed Guidance"}</span>
                <ArrowRightIcon size={16} color="#FFFFFF" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GuidedAssistance;
