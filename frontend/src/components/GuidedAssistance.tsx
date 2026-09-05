import React, { useState } from "react";
import type { LanguageCode } from "../types";

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
  icon: string;
  step1Question: { en: string; hi: string; mr: string };
  step1Options: StepOption[];
  step2Question: { en: string; hi: string; mr: string };
  step2Options: StepOption[];
  checklist: Array<{ en: string; hi: string; mr: string }>;
  promptTemplate: (opt1: string, opt2: string) => string;
}

const FLOW_CONFIGS: Record<string, FlowConfig> = {
  crop_damage: {
    titleEn: "PMFBY Crop Damage Assistance",
    titleHi: "पीएमएफबीवाई फसल नुकसान सहायता",
    titleMr: "PMFBY पीक नुकसान मदत",
    icon: "🌾",
    step1Question: {
      en: "What type of damage occurred?",
      hi: "किस प्रकार का नुकसान हुआ है?",
      mr: "नुकसान कशामुळे झाले आहे?",
    },
    step1Options: [
      { id: "rain", en: "Excessive Rain / Flood", hi: "अत्यधिक वर्षा / बाढ़", mr: "अतिवृष्टी / पूर" },
      { id: "hail", en: "Hailstorm", hi: "ओला वृष्टि", mr: "गारपीट" },
      { id: "drought", en: "Dry Spell / Drought", hi: "सूखा / वर्षा की कमी", mr: "दुष्काळ / पावसाचा खंड" },
      { id: "pest", en: "Pest / Disease Attack", hi: "कीट / रोग का प्रकोप", mr: "कीड / रोग प्रादुर्भाव" },
    ],
    step2Question: {
      en: "What stage is the crop in?",
      hi: "फसल किस चरण में है?",
      mr: "पीक कोणत्या टप्प्यात आहे?",
    },
    step2Options: [
      { id: "standing", en: "Standing Crop", hi: "खड़ी फसल", mr: "उभे पीक" },
      { id: "harvested", en: "Cut & Spread (Post-Harvest)", hi: "कटी हुई फसल (कटाई के बाद)", mr: "कापणी केलेले पीक" },
      { id: "sowing", en: "Prevented Sowing", hi: "बुआई न हो पाना", mr: "पेरणी न होणे" },
    ],
    checklist: [
      { en: "Intimate within 72 hours of damage", hi: "नुकसान के 72 घंटे के भीतर सूचित करें", mr: "७२ तासांच्या आत विमा कंपनीस कळवा" },
      { en: "Keep 7/12 land extract & bank passbook ready", hi: "7/12 भूमि विवरण एवं बैंक पासबुक रखें", mr: "७/१२ उतारा व बँक पासबुक तयार ठेवा" },
      { en: "Take geotagged photos of damaged crop", hi: "क्षतिग्रस्त फसल की तस्वीरें लें", mr: "नुकसानग्रस्त पिकाचे फोटो काढा" },
      { en: "Contact PACS / Agriculture Officer / Toll-free 14447", hi: "पैक्स / कृषि अधिकारी / टोल-फ्री 14447 पर संपर्क करें", mr: "PACS / कृषी अधिकारी / टोल-फ्री १४४४७ वर संपर्क साधा" },
    ],
    promptTemplate: (opt1, opt2) =>
      `My crop suffered ${opt1} damage during ${opt2} stage. What are the exact steps and documents required to claim PMFBY crop insurance compensation?`,
  },
  pacs_help: {
    titleEn: "PACS Service Guidance",
    titleHi: "पैक्स (PACS) सेवा मार्गदर्शन",
    titleMr: "PACS सेवा मार्गदर्शन",
    icon: "🏛️",
    step1Question: {
      en: "Which service do you need?",
      hi: "आपको किस सेवा की आवश्यकता है?",
      mr: "तुम्हाला कोणती सेवा हवी आहे?",
    },
    step1Options: [
      { id: "loan", en: "KCC Short-term Crop Loan", hi: "केसीसी अल्पकालिक फसल ऋण", mr: "KCC पीक कर्ज" },
      { id: "inputs", en: "Seeds & Fertilizer Purchase", hi: "बीज एवं उर्वरक खरीद", mr: "बियाणे व खते खरेदी" },
      { id: "storage", en: "Warehouse / Storage Facility", hi: "गोदाम / भंडारण सुविधा", mr: "गोदाम / साठवणूक सुविधा" },
      { id: "membership", en: "New PACS Membership", hi: "नवीन पैक्स सदस्यता", mr: "नवीन PACS सभासदत्व" },
    ],
    step2Question: {
      en: "Are you an existing PACS member?",
      hi: "क्या आप वर्तमान में पैक्स के सदस्य हैं?",
      mr: "तुम्ही सध्या PACS चे सभासद आहात का?",
    },
    step2Options: [
      { id: "yes", en: "Yes, active member", hi: "हाँ, सक्रिय सदस्य", mr: "होय, सक्रिय सभासद" },
      { id: "no", en: "No, want to apply", hi: "नहीं, आवेदन करना चाहता हूँ", mr: "नाही, अर्ज करायचा आहे" },
    ],
    checklist: [
      { en: "Aadhaar Card & PAN Card", hi: "आधार कार्ड एवं पैन कार्ड", mr: "आधार कार्ड व पॅन कार्ड" },
      { en: "7/12 & 8A Land Records", hi: "7/12 एवं 8A भूमि दस्तावेज", mr: "७/१२ व ८अ उतारा" },
      { en: "No-dues certificate from nearby banks", hi: "अन्य बैंकों से बकाया न होने का प्रमाण पत्र", mr: "इतर बँकांचे थकबाकी नसल्याचे प्रमाणपत्र" },
    ],
    promptTemplate: (opt1, opt2) =>
      `I need assistance with ${opt1} at PACS as a ${opt2}. What is the process, interest subvention benefit, and required documentation?`,
  },
  coop_rule: {
    titleEn: "Cooperative Rules & By-laws",
    titleHi: "सहकारी नियम एवं उपनियम",
    titleMr: "सहकारी संस्था नियम व उपविधी",
    icon: "📜",
    step1Question: {
      en: "Which area of governance do you want to understand?",
      hi: "आप शासन के किस क्षेत्र को समझना चाहते हैं?",
      mr: "तुम्हाला कोणत्या विषयाबाबत माहिती हवी आहे?",
    },
    step1Options: [
      { id: "rights", en: "Member Rights & Voting", hi: "सदस्य अधिकार एवं मतदान", mr: "सभासद अधिकार व मतदान" },
      { id: "election", en: "Committee Elections & Tenure", hi: "समिति चुनाव एवं कार्यकाल", mr: "संचालक मंडळ निवडणूक व मुदत" },
      { id: "audit", en: "Annual General Body & Audit", hi: "वार्षिक साधारण सभा एवं ऑडिट", mr: "वार्षिक सर्वसाधारण सभा व ऑडिट" },
      { id: "expulsion", en: "Member Disqualification / Expulsion", hi: "सदस्य अयोग्यता / निष्कासन", mr: "सभासद अपात्रता / हकालपट्टी" },
    ],
    step2Question: {
      en: "Which cooperative type?",
      hi: "किस प्रकार की सहकारी संस्था?",
      mr: "कोणत्या प्रकारची सहकारी संस्था?",
    },
    step2Options: [
      { id: "pacs_soc", en: "PACS / Agricultural Credit", hi: "पैक्स / कृषि साख समिति", mr: "PACS / कृषी पतसंस्था" },
      { id: "housing", en: "Housing Cooperative Society", hi: "आवास सहकारी समिति", mr: "गृहनिर्माण संस्था" },
      { id: "other_soc", en: "Other Cooperative Society", hi: "अन्य सहकारी समिति", mr: "इतर सहकारी संस्था" },
    ],
    checklist: [
      { en: "Check Maharashtra Cooperative Societies Act provisions", hi: "महाराष्ट्र सहकारी अधिनियम प्रावधान देखें", mr: "महाराष्ट्र सहकारी संस्था कायद्यातील तरतुदी तपासा" },
      { en: "Refer to Model By-law Section 22 to 35", hi: "मॉडल उपनियम धारा 22 से 35 देखें", mr: "मॉडेल उपविधी कलम २२ ते ३५ पहा" },
    ],
    promptTemplate: (opt1, opt2) =>
      `Explain the Maharashtra Cooperative Societies Act rules and standard by-laws regarding ${opt1} for a ${opt2}.`,
  },
  financial_guidance: {
    titleEn: "Rural Financial Literacy Guidance",
    titleHi: "ग्रामीण वित्तीय साक्षरता मार्गदर्शन",
    titleMr: "ग्रामीण आर्थिक साक्षरता मार्गदर्शन",
    icon: "🏦",
    step1Question: {
      en: "What financial topic do you need help with?",
      hi: "आपको किस वित्तीय विषय पर सहायता चाहिए?",
      mr: "तुम्हाला कोणत्या आर्थिक विषयावर माहिती हवी आहे?",
    },
    step1Options: [
      { id: "kcc", en: "Kisan Credit Card (KCC) Interest Subvention", hi: "केसीसी ब्याज अनुदान योजना", mr: "KCC व्याज सवलत योजना" },
      { id: "loan_repay", en: "Loan Repayment & Credit Score", hi: "ऋण पुनर्भुगतान एवं क्रेडिट स्कोर", mr: "कर्ज परतफेड व सिबिल स्कोर" },
      { id: "deposit", en: "Cooperative Bank Fixed Deposits", hi: "सहकारी बैंक सावधि जमा (FD)", mr: "सहकारी बँक मुदत ठेव (FD)" },
      { id: "insurance", en: "Micro-Insurance & Pension Schemes", hi: "सूक्ष्म बीमा एवं पेंशन योजनाएं", mr: "सूक्ष्म विमा व पेन्शन योजना" },
    ],
    step2Question: {
      en: "What is your primary goal?",
      hi: "आपका मुख्य उद्देश्य क्या है?",
      mr: "तुमचा मुख्य उद्देश काय आहे?",
    },
    step2Options: [
      { id: "save_cost", en: "Reduce interest burden", hi: "ब्याज का बोझ कम करना", mr: "व्याज भार कमी करणे" },
      { id: "borrow", en: "Apply for new credit", hi: "नए ऋण के लिए आवेदन करना", mr: "नवीन कर्जासाठी अर्ज करणे" },
      { id: "safe_save", en: "Safe savings & investment", hi: "सुरक्षित बचत एवं निवेश", mr: "सुरक्षित बचत व गुंतवणूक" },
    ],
    checklist: [
      { en: "Timely repayment earns 3% interest subvention", hi: "समय पर भुगतान करने पर 3% अतिरिक्त ब्याज छूट", mr: "वेळेवर परतफेड केल्यास ३% अतिरिक्त व्याज सवलत" },
      { en: "Always obtain official computerised receipt", hi: "हमेशा आधिकारिक कम्प्यूटरीकृत रसीद प्राप्त करें", mr: "नेहमी संगणकीकृत पावती मिळवा" },
    ],
    promptTemplate: (opt1, opt2) =>
      `Provide financial literacy guidance on ${opt1} to help ${opt2}. Explain the benefits, interest rates, and safety precautions.`,
  },
  schemes_entry: {
    titleEn: "Ministry of Cooperation Schemes",
    titleHi: "सहकार मंत्रालय योजनाएं",
    titleMr: "सहकार मंत्रालय योजना",
    icon: "🏛️",
    step1Question: {
      en: "Which scheme domain interests you?",
      hi: "आप किस योजना क्षेत्र में रुचि रखते हैं?",
      mr: "तुम्हाला कोणत्या योजनेत रस आहे?",
    },
    step1Options: [
      { id: "pacs_comp", en: "PACS Computerization & ERP", hi: "पैक्स संगणकीकरण एवं ईआरपी", mr: "PACS संगणकीकरण व संगणकीय प्रणाली" },
      { id: "grain_storage", en: "World's Largest Grain Storage Plan", hi: "विश्व की सबसे बड़ी अन्न भंडारण योजना", mr: "जगातील सर्वात मोठी धान्य साठवणूक योजना" },
      { id: "seed_organic", en: "National Organic / Seed Cooperatives", hi: "राष्ट्रीय जैविक / बीज सहकारी संस्थाएं", mr: "राष्ट्रीय सेंद्रिय / बियाणे सहकारी संस्था" },
      { id: "common_service", en: "PACS as Common Service Centers (CSC)", hi: "सामान्य सेवा केंद्र (CSC) के रूप में पैक्स", mr: "सीएससी (CSC) म्हणून PACS सेवा" },
    ],
    step2Question: {
      en: "What information do you need?",
      hi: "आपको क्या जानकारी चाहिए?",
      mr: "तुम्हाला कोणती माहिती हवी आहे?",
    },
    step2Options: [
      { id: "eligibility", en: "Eligibility & Benefits", hi: "पात्रता एवं लाभ", mr: "पात्रता व फायदे" },
      { id: "apply", en: "How to apply / Participate", hi: "आवेदन / भागीदारी कैसे करें", mr: "अर्ज / सहभाग कसा घ्यावा" },
    ],
    checklist: [
      { en: "Check Central Registrar / Ministry portal details", hi: "केंद्रीय निबंधक / मंत्रालय पोर्टल देखें", mr: "केंद्रीय निबंधक / मंत्रालय पोर्टल तपासा" },
      { en: "Contact local District Central Cooperative Bank (DCCB)", hi: "स्थानीय जिला मध्यवर्ती बैंक (DCCB) से संपर्क करें", mr: "जिल्हा मध्यवर्ती सहकारी बँकेशी संपर्क साधा" },
    ],
    promptTemplate: (opt1, opt2) =>
      `Explain the Ministry of Cooperation scheme regarding ${opt1}, focusing on ${opt2} for cooperative members.`,
  },
};

const GuidedAssistance: React.FC<Props> = ({ flowType, language, onAskAI, onBack }) => {
  const config = FLOW_CONFIGS[flowType] ?? FLOW_CONFIGS.crop_damage;

  const [step1Val, setStep1Val] = useState<StepOption | null>(config.step1Options[0] ?? null);
  const [step2Val, setStep2Val] = useState<StepOption | null>(config.step2Options[0] ?? null);
  const [currentStep, setCurrentStep] = useState<number>(1);

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
      {/* Header Bar */}
      <div className="wizard-header">
        <button type="button" className="wizard-back-btn" onClick={onBack} aria-label="Go back">
          ← {language === "hi" ? "वापस" : language === "mr" ? "मागे" : "Back"}
        </button>
        <div className="wizard-title-group">
          <span className="wizard-icon">{config.icon}</span>
          <h3 className="wizard-title">{title}</h3>
        </div>
      </div>

      {/* Progress Indicator */}
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
            {language === "hi" ? "विवरण" : language === "mr" ? "तपशील" : "Details"}
          </span>
        </div>
        <div className="progress-line" />
        <div className={`progress-step ${currentStep >= 3 ? "progress-step--active" : ""}`}>
          <span className="step-num">3</span>
          <span className="step-label">
            {language === "hi" ? "कदम व कागजात" : language === "mr" ? "पायऱ्या व कागदपत्रे" : "Action Plan"}
          </span>
        </div>
      </div>

      {/* Step Content */}
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
                  <span className="opt-radio">{step1Val?.id === opt.id ? "●" : "○"}</span>
                  <span className="opt-text">{opt[language] ?? opt.en}</span>
                </button>
              ))}
            </div>
            <button
              type="button"
              className="wizard-next-btn"
              onClick={() => setCurrentStep(2)}
            >
              {language === "hi" ? "आगे बढ़ें →" : language === "mr" ? "पुढे जा →" : "Next Step →"}
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
                  <span className="opt-radio">{step2Val?.id === opt.id ? "●" : "○"}</span>
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
                {language === "hi" ? "मार्गदर्शन देखें →" : language === "mr" ? "मार्गदर्शन पहा →" : "View Guidance →"}
              </button>
            </div>
          </div>
        )}

        {currentStep === 3 && (
          <div className="wizard-step-panel">
            <h4 className="step-question">
              {language === "hi"
                ? "जरूरी दस्तावेज एवं अगले कदम"
                : language === "mr"
                ? "महत्त्वाची कागदपत्रे व पुढील पायऱ्या"
                : "Required Checklist & Immediate Actions"}
            </h4>

            <div className="checklist-box">
              <span className="checklist-title">
                📋 {language === "hi" ? "आवश्यक सूची" : language === "mr" ? "तपासाची यादी" : "Checklist"}
              </span>
              <ul className="checklist-items">
                {config.checklist.map((item, idx) => (
                  <li key={idx}>✓ {item[language] ?? item.en}</li>
                ))}
              </ul>
            </div>

            <div className="wizard-summary-callout">
              <span className="callout-heading">
                💡 {language === "hi" ? "सहकारसेतु एआई सहायता" : language === "mr" ? "सहकारसेतू एआय मदत" : "SahkaarSetu Grounded Guidance"}
              </span>
              <p className="callout-text">
                {language === "hi"
                  ? "अब आप अपनी चयनित स्थिति के अनुसार सहकारसेतु से विस्तृत आधिकारिक उत्तर प्राप्त कर सकते हैं।"
                  : language === "mr"
                  ? "आता तुम्ही तुमच्या निवडलेल्या परिस्थितीनुसार सहकारसेतूकडून सविस्तर अधिकृत उत्तर मिळवू शकता."
                  : "Click below to query our grounded RAG knowledge base for specific clauses, claim numbers, and official sources."}
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
                🤖 {language === "hi" ? "एआई से पूरा उत्तर प्राप्त करें" : language === "mr" ? "AI कडून सविस्तर उत्तर घ्या" : "Get Detailed AI Answer →"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GuidedAssistance;
