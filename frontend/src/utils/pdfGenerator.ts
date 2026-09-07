/**
 * pdfGenerator.ts
 *
 * Professional, language-aware Smart Guidance PDF generator for SahkaarSetu (SIH26088).
 * Generates a clean, publication-grade document directly from the SAME structured AI response.
 *
 * Design Guidelines:
 * - Restrained branding: Deep Teal (#126B62), Warm Cream (#F7F4EA), Dark Text (#173C3A), Gold Accent (#D6A52F).
 * - Full Devanagari (Hindi, Marathi) & Latin font support via Google Fonts + system fallback.
 * - Dynamic sections: Only renders sections that actually exist in the structured answer.
 * - Meaningful sanitized filename: sahkaarsetu-[sanitized-title].pdf
 * - Verified clickable sources & concise official disclaimer.
 */

export interface PdfGuidanceInput {
  title?: string;
  question?: string;
  language?: string; // 'mr' | 'hi' | 'en'
  domainLabel?: string;
  summary: string;
  description?: string;
  keyFacts?: Array<{ label: string; value: string }>;
  steps?: Array<{ stepNum: number; title: string; description?: string }>;
  documents?: string[];
  contacts?: Array<{ label: string; value: string; url?: string }>;
  eligibility?: string[];
  warnings?: string[];
  nextSteps?: string[];
  sources?: Array<{ title: string; authority?: string; url?: string }>;
}

export async function generateGuidancePdf(input: PdfGuidanceInput): Promise<void> {
  const lang = input.language || "en";

  // Localized section headers
  const labels = {
    platformName: "SAHKAARSETU",
    platformSub:
      lang === "hi"
        ? "बहुभाषी सहकार एवं कृषि सहायता मंच"
        : lang === "mr"
        ? "बहुभाषिक सहकार व कृषी मदत व्यासपीठ"
        : "Multilingual Cooperative & Agricultural Assistance Platform",
    docBadge:
      lang === "hi"
        ? "आधिकारिक मार्गदर्शन नोट"
        : lang === "mr"
        ? "अधिकृत मार्गदर्शन नोंद"
        : "Official Guidance Note",
    userQuestion:
      lang === "hi"
        ? "आपका प्रश्न"
        : lang === "mr"
        ? "आपला प्रश्न"
        : "YOUR QUESTION",
    directAnswer:
      lang === "hi"
        ? "मुख्य उत्तर एवं सारांश"
        : lang === "mr"
        ? "थेट उत्तर व सारांश"
        : "DIRECT ANSWER & SUMMARY",
    keyFacts:
      lang === "hi"
        ? "मुख्य विवरण एवं दरें"
        : lang === "mr"
        ? "महत्त्वाचे तपशील व दर"
        : "KEY HIGHLIGHTS & DETAILS",
    procedure:
      lang === "hi"
        ? "चरण-दर-चरण प्रक्रिया"
        : lang === "mr"
        ? "टप्पा-निहाय कार्यपद्धती"
        : "STEP-BY-STEP PROCEDURE",
    documents:
      lang === "hi"
        ? "आवश्यक दस्तावेजों की चेकलिस्ट"
        : lang === "mr"
        ? "आवश्यक कागदपत्रांची चेकलिस्ट"
        : "REQUIRED DOCUMENTS CHECKLIST",
    contacts:
      lang === "hi"
        ? "आधिकारिक संपर्क एवं हेल्पलाइन"
        : lang === "mr"
        ? "अधिकृत संपर्क व हेल्पलाईन"
        : "OFFICIAL CONTACT & HELPLINES",
    eligibility:
      lang === "hi"
        ? "पात्रता मापदंड"
        : lang === "mr"
        ? "पात्रता निकष"
        : "ELIGIBILITY CRITERIA",
    warnings:
      lang === "hi"
        ? "महत्वपूर्ण सूचना एवं समय सीमा"
        : lang === "mr"
        ? "महत्त्वाच्या सूचना व मुदत"
        : "IMPORTANT NOTICE & DEADLINES",
    nextSteps:
      lang === "hi"
        ? "अनुशंसित अगला कदम"
        : lang === "mr"
        ? "पुढील अनुशंसित कृती"
        : "RECOMMENDED NEXT STEP",
    sources:
      lang === "hi"
        ? "सत्यापित आधिकारिक स्रोत"
        : lang === "mr"
        ? "सत्यापित अधिकृत स्रोत"
        : "VERIFIED OFFICIAL SOURCES",
    disclaimer:
      lang === "hi"
        ? "यह मार्गदर्शन सहकारसेतू द्वारा उपलब्ध आधिकारिक स्रोतों के आधार पर तैयार किया गया है। कृपया कोई भी कदम उठाने से पहले संबंधित आधिकारिक पोर्टल या विभाग से वर्तमान नियमों की पुष्टि करें।"
        : lang === "mr"
        ? "हे मार्गदर्शन सहकारसेतू द्वारे उपलब्ध अधिकृत स्रोतांच्या आधारे तयार करण्यात आले आहे. कृपया कोणतीही कृती करण्यापूर्वी संबंधित अधिकृत पोर्टल किंवा विभागाकडून वर्तमान नियमांची पडताळणी करावी."
        : "This guidance is based on cited official information available to SAHKAARSETU at the time of generation. Please verify current requirements with the official source before taking action.",
    footer:
      "SahkaarSetu AI • Ministry of Cooperation & Agriculture Assistance • Generated on " +
      new Date().toLocaleDateString(),
  };

  // Meaningful sanitized filename: sahkaarsetu-[sanitized-title].pdf
  const rawTitle = (input.title || input.domainLabel || "Guidance")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 35) || "guidance";
  const fileName = `sahkaarsetu-${rawTitle}`;

  // Build clean HTML print document
  const htmlDoc = `
    <!DOCTYPE html>
    <html lang="${lang}">
    <head>
      <meta charset="UTF-8">
      <title>${fileName}</title>
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700;800&family=Noto+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
      <style>
        @page { size: A4; margin: 12mm; }
        * { box-sizing: border-box; }
        body {
          font-family: 'Noto Sans Devanagari', 'Noto Sans', system-ui, -apple-system, sans-serif;
          color: #173C3A;
          background: #FFFFFF;
          margin: 0;
          padding: 16px;
          line-height: 1.5;
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }
        .pdf-container {
          max-width: 800px;
          margin: 0 auto;
          border: 2px solid #126B62;
          border-radius: 8px;
          padding: 24px;
          background: #FFFFFF;
        }
        .header-top {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          border-bottom: 2px solid #126B62;
          padding-bottom: 14px;
          margin-bottom: 16px;
        }
        .brand-title {
          font-size: 22px;
          font-weight: 800;
          color: #126B62;
          margin: 0;
          letter-spacing: -0.5px;
        }
        .brand-subtitle {
          font-size: 11.5px;
          color: #1B806F;
          font-weight: 600;
          margin: 2px 0 0 0;
        }
        .badge-pill {
          background: #F7F4EA;
          border: 1px solid #D6A52F;
          color: #126B62;
          font-size: 11px;
          font-weight: 700;
          padding: 4px 10px;
          border-radius: 4px;
          text-align: right;
        }
        .main-topic-title {
          font-size: 17px;
          font-weight: 800;
          color: #126B62;
          margin: 0 0 14px 0;
          padding-bottom: 8px;
          border-bottom: 1px solid #D9E2DE;
        }
        .question-box {
          background: #F7F4EA;
          border-left: 4px solid #D6A52F;
          padding: 10px 14px;
          border-radius: 0 6px 6px 0;
          margin-bottom: 16px;
        }
        .question-lbl {
          font-size: 10px;
          font-weight: 800;
          color: #D6A52F;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .question-txt {
          font-size: 13px;
          font-weight: 600;
          color: #173C3A;
          margin-top: 2px;
        }
        .section-block {
          margin-bottom: 16px;
        }
        .section-heading {
          font-size: 11.5px;
          font-weight: 800;
          color: #126B62;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          border-bottom: 1px solid #D9E2DE;
          padding-bottom: 4px;
          margin: 0 0 8px 0;
        }
        .summary-text {
          font-size: 13px;
          line-height: 1.6;
          color: #173C3A;
          margin: 0 0 8px 0;
        }
        .facts-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
          margin-top: 6px;
        }
        .fact-card {
          background: #F7F4EA;
          border: 1px solid #D9E2DE;
          border-radius: 6px;
          padding: 8px 10px;
        }
        .fact-k { font-size: 10.5px; font-weight: 600; color: #1B806F; }
        .fact-v { font-size: 12.5px; font-weight: 800; color: #126B62; margin-top: 1px; }

        .step-row {
          display: flex;
          gap: 10px;
          background: #FFFFFF;
          border: 1px solid #D9E2DE;
          border-radius: 6px;
          padding: 8px 12px;
          margin-bottom: 6px;
        }
        .step-badge {
          width: 26px;
          height: 26px;
          border-radius: 4px;
          background: #126B62;
          color: #FFFFFF;
          font-size: 11px;
          font-weight: 800;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .step-content-title { font-size: 12.5px; font-weight: 700; color: #173C3A; }
        .step-content-desc { font-size: 12px; color: #444444; margin-top: 2px; }

        .checklist-item {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          font-size: 12.5px;
          margin-bottom: 5px;
          color: #173C3A;
        }
        .checkbox-sq {
          color: #126B62;
          font-weight: 800;
          font-size: 13px;
          line-height: 1;
        }

        .warning-container {
          background: #FFFDF5;
          border: 1px solid #D6A52F;
          border-radius: 6px;
          padding: 10px 14px;
          margin-bottom: 16px;
        }
        .warning-title {
          font-size: 11px;
          font-weight: 800;
          color: #D6A52F;
          text-transform: uppercase;
          margin-bottom: 4px;
        }
        .warning-list {
          margin: 0;
          padding-left: 16px;
          font-size: 12px;
          color: #5A4400;
        }

        .sources-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        .source-entry {
          font-size: 11.5px;
          color: #173C3A;
          margin-bottom: 4px;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .source-entry a {
          color: #126B62;
          text-decoration: underline;
        }
        .auth-tag {
          font-size: 9.5px;
          font-weight: 700;
          background: #EAF5F3;
          color: #126B62;
          padding: 1px 6px;
          border-radius: 3px;
        }

        .disclaimer-box {
          border-top: 1px solid #D9E2DE;
          padding-top: 10px;
          margin-top: 18px;
          font-size: 10px;
          color: #555555;
          line-height: 1.4;
          text-align: justify;
        }
        .footer-bar {
          margin-top: 12px;
          text-align: center;
          font-size: 10px;
          font-weight: 600;
          color: #1B806F;
        }
        @media print {
          body { padding: 0; }
          .pdf-container { border: none; max-width: 100%; padding: 0; }
        }
      </style>
    </head>
    <body>
      <div class="pdf-container">
        <!-- Top Header Banner -->
        <div class="header-top">
          <div>
            <h1 class="brand-title">${labels.platformName}</h1>
            <p class="brand-subtitle">${labels.platformSub}</p>
          </div>
          <div class="badge-pill">
            ${labels.docBadge}
            ${input.domainLabel ? `<div style="font-size: 9.5px; color: #555; margin-top: 2px;">${input.domainLabel}</div>` : ""}
          </div>
        </div>

        <!-- Dynamic Title -->
        ${
          input.title
            ? `<div class="main-topic-title">${input.title}</div>`
            : input.domainLabel
            ? `<div class="main-topic-title">${input.domainLabel}</div>`
            : ""
        }

        <!-- User Question Section -->
        ${
          input.question
            ? `
          <div class="question-box">
            <div class="question-lbl">${labels.userQuestion}</div>
            <div class="question-txt">"${input.question}"</div>
          </div>
        `
            : ""
        }

        <!-- Direct Answer / Summary Section -->
        ${
          input.summary
            ? `
          <div class="section-block">
            <div class="section-heading">${labels.directAnswer}</div>
            <p class="summary-text">${input.summary}</p>
            ${
              input.description
                ? `<p class="summary-text" style="color: #333;">${input.description}</p>`
                : ""
            }
          </div>
        `
            : ""
        }

        <!-- Key Details / Highlights (Only if present) -->
        ${
          input.keyFacts && input.keyFacts.length > 0
            ? `
          <div class="section-block">
            <div class="section-heading">${labels.keyFacts}</div>
            <div class="facts-grid">
              ${input.keyFacts
                .map(
                  (f) => `
                <div class="fact-card">
                  <div class="fact-k">${f.label}</div>
                  <div class="fact-v">${f.value}</div>
                </div>
              `
                )
                .join("")}
            </div>
          </div>
        `
            : ""
        }

        <!-- Step-by-Step Procedure (Only if present) -->
        ${
          input.steps && input.steps.length > 0
            ? `
          <div class="section-block">
            <div class="section-heading">${labels.procedure}</div>
            <div>
              ${input.steps
                .map(
                  (st) => `
                <div class="step-row">
                  <div class="step-badge">${String(st.stepNum).padStart(2, "0")}</div>
                  <div>
                    <div class="step-content-title">${st.title}</div>
                    ${st.description ? `<div class="step-content-desc">${st.description}</div>` : ""}
                  </div>
                </div>
              `
                )
                .join("")}
            </div>
          </div>
        `
            : ""
        }

        <!-- Documents Checklist (Only if present) -->
        ${
          input.documents && input.documents.length > 0
            ? `
          <div class="section-block">
            <div class="section-heading">${labels.documents}</div>
            <div style="background: #F7F4EA; border: 1px solid #D9E2DE; border-radius: 6px; padding: 10px 14px;">
              ${input.documents
                .map(
                  (doc) => `
                <div class="checklist-item">
                  <span class="checkbox-sq">☐</span>
                  <span>${doc}</span>
                </div>
              `
                )
                .join("")}
            </div>
          </div>
        `
            : ""
        }

        <!-- Eligibility Criteria (Only if present) -->
        ${
          input.eligibility && input.eligibility.length > 0
            ? `
          <div class="section-block">
            <div class="section-heading">${labels.eligibility}</div>
            <ul style="margin: 0; padding-left: 18px; font-size: 12.5px; color: #173C3A;">
              ${input.eligibility.map((e) => `<li style="margin-bottom: 3px;">${e}</li>`).join("")}
            </ul>
          </div>
        `
            : ""
        }

        <!-- Important Notice / Warnings (Only if present) -->
        ${
          input.warnings && input.warnings.length > 0
            ? `
          <div class="warning-container">
            <div class="warning-title">${labels.warnings}</div>
            <ul class="warning-list">
              ${input.warnings.map((w) => `<li>${w}</li>`).join("")}
            </ul>
          </div>
        `
            : ""
        }

        <!-- Recommended Next Step (Only if present) -->
        ${
          input.nextSteps && input.nextSteps.length > 0
            ? `
          <div class="section-block">
            <div class="section-heading">${labels.nextSteps}</div>
            <ol style="margin: 0; padding-left: 18px; font-size: 12.5px; color: #173C3A;">
              ${input.nextSteps.map((ns) => `<li style="margin-bottom: 3px;"><strong>${ns}</strong></li>`).join("")}
            </ol>
          </div>
        `
            : ""
        }

        <!-- Official Verified Sources (Only if present) -->
        ${
          input.sources && input.sources.length > 0
            ? `
          <div class="section-block">
            <div class="section-heading">${labels.sources}</div>
            <ul class="sources-list">
              ${input.sources
                .map(
                  (s) => `
                <li class="source-entry">
                  <span>✓</span>
                  <strong>${s.title}</strong>
                  ${s.authority ? `<span class="auth-tag">${s.authority}</span>` : ""}
                  ${s.url ? `<a href="${s.url}" target="_blank">${s.url}</a>` : ""}
                </li>
              `
                )
                .join("")}
            </ul>
          </div>
        `
            : ""
        }

        <!-- Concise Official Disclaimer -->
        <div class="disclaimer-box">
          <strong>Notice:</strong> ${labels.disclaimer}
        </div>

        <div class="footer-bar">${labels.footer}</div>
      </div>

      <script>
        window.onload = function() {
          setTimeout(function() {
            window.print();
          }, 300);
        };
      </script>
    </body>
    </html>
  `;

  // Create printable Blob document
  const blob = new Blob([htmlDoc], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const win = window.open(url, "_blank");
  if (!win) {
    // Fallback if popup blocked
    const link = document.createElement("a");
    link.href = url;
    link.download = `${fileName}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
