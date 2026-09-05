/**
 * pdfGenerator.ts
 *
 * Professional, language-aware Guidance PDF generator for SahkaarSetu.
 * Generates a clean document directly from structured guidance response data.
 *
 * Brand Palette:
 * - Deep Teal: #126B62
 * - Cooperative Green: #1B806F
 * - Harvest Gold: #D6A52F
 * - Warm Ivory: #F7F4EA
 * - Dark Text: #173C3A
 * - Light Border: #D9E2DE
 */

export interface PdfGuidanceInput {
  question?: string;
  language?: string; // 'mr' | 'hi' | 'en'
  domainLabel: string;
  summary: string;
  description?: string;
  keyFacts?: Array<{ label: string; value: string }>;
  steps?: Array<{ stepNum: number; title: string; description?: string }>;
  warnings?: string[];
  nextSteps?: string[];
  sources?: Array<{ title: string; authority?: string; url?: string }>;
}

export async function generateGuidancePdf(input: PdfGuidanceInput): Promise<void> {
  const lang = input.language || "mr";

  // Section titles localized
  const labels = {
    docTitle:
      lang === "hi"
        ? "सहकार सेतू - आधिकारिक मार्गदर्शन नोट"
        : lang === "en"
        ? "SahkaarSetu Official Guidance Note"
        : "सहकार सेतू - अधिकृत मार्गदर्शन नोंद",
    subTitle:
      lang === "hi"
        ? "बहुभाषी सहकार सहायता मंच"
        : lang === "en"
        ? "Multilingual Cooperative Assistance Platform"
        : "बहुभाषिक सहकार मदत व्यासपीठ",
    userQuestion:
      lang === "hi"
        ? "आपका प्रश्न / विषय:"
        : lang === "en"
        ? "YOUR QUESTION / TOPIC:"
        : "आपला प्रश्न / विषय:",
    guidanceOverview:
      lang === "hi"
        ? "मार्गदर्शन एवं विवरण:"
        : lang === "en"
        ? "OFFICIAL GUIDANCE & DETAILS:"
        : "अधिकृत मार्गदर्शन व माहिती:",
    keyFacts:
      lang === "hi"
        ? "मुख्य विवरण एवं दरें:"
        : lang === "en"
        ? "KEY HIGHLIGHTS & RATES:"
        : "महत्त्वाचे तपशील व दर:",
    steps:
      lang === "hi"
        ? "प्रक्रिया के चरण:"
        : lang === "en"
        ? "STEP-BY-STEP PROCEDURE:"
        : "नुकसान भरपाई / अर्ज प्रक्रिया:",
    warnings:
      lang === "hi"
        ? "महत्वपूर्ण सूचना:"
        : lang === "en"
        ? "IMPORTANT NOTICE / DEADLINE:"
        : "महत्त्वाच्या सूचना व मुदत:",
    nextSteps:
      lang === "hi"
        ? "आगे क्या करें (अनुशंसित कदम):"
        : lang === "en"
        ? "WHAT TO DO NEXT (RECOMMENDED ACTIONS):"
        : "पुढे काय करावे (अनुशंसित कृती):",
    sources:
      lang === "hi"
        ? "अधिकृत स्रोत एवं संदर्भ:"
        : lang === "en"
        ? "OFFICIAL SOURCES & REFERENCES:"
        : "अधिकृत स्रोत व संदर्भ:",
    footer: "SahkaarSetu • Understand. Get Guided. Move Forward. • " + new Date().toLocaleDateString(),
  };

  const cleanDomain = input.domainLabel
    .replace(/[^a-zA-Z0-9]/g, "_")
    .replace(/_+/g, "_")
    .slice(0, 20);
  const langSuffix = lang === "mr" ? "Marathi" : lang === "hi" ? "Hindi" : "English";
  const fileName = `SahkaarSetu_${cleanDomain}_Guidance_${langSuffix}`;

  // HTML Printable / PDF Document Layout
  const htmlDoc = `
    <!DOCTYPE html>
    <html lang="${lang}">
    <head>
      <meta charset="UTF-8">
      <title>${fileName}</title>
      <style>
        @page { size: A4; margin: 12mm; }
        body {
          font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          color: #173C3A;
          background: #FFFFFF;
          margin: 0;
          padding: 20px;
          box-sizing: border-box;
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }
        .pdf-card {
          border: 2px solid #126B62;
          border-radius: 8px;
          padding: 24px;
          background: #FFFFFF;
        }
        .header-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-bottom: 2px solid #D9E2DE;
          padding-bottom: 16px;
          margin-bottom: 20px;
        }
        .brand-name {
          margin: 0;
          font-size: 24px;
          font-weight: 800;
          color: #126B62;
          letter-spacing: -0.5px;
        }
        .brand-sub {
          margin: 2px 0 0 0;
          font-size: 12px;
          font-weight: 600;
          color: #1B806F;
        }
        .domain-tag {
          background: #F7F4EA;
          border: 1px solid #D6A52F;
          color: #126B62;
          font-size: 11px;
          font-weight: 700;
          padding: 4px 10px;
          border-radius: 4px;
        }
        .doc-banner {
          text-align: center;
          margin-bottom: 20px;
          background: #F7F4EA;
          padding: 10px;
          border-radius: 6px;
        }
        .doc-banner h2 {
          margin: 0;
          font-size: 15px;
          font-weight: 700;
          color: #126B62;
        }
        .user-q-box {
          margin-bottom: 18px;
          background: #F7F4EA;
          border-left: 4px solid #D6A52F;
          padding: 10px 14px;
          border-radius: 0 6px 6px 0;
        }
        .q-label {
          font-size: 11px;
          font-weight: 800;
          color: #D6A52F;
          text-transform: uppercase;
          margin-bottom: 4px;
        }
        .q-text {
          font-size: 13.5px;
          font-weight: 600;
          color: #173C3A;
        }
        .section-label {
          font-size: 12px;
          font-weight: 800;
          color: #126B62;
          text-transform: uppercase;
          margin-bottom: 6px;
          border-bottom: 1px solid #D9E2DE;
          padding-bottom: 4px;
        }
        .facts-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 10px;
          margin-bottom: 20px;
        }
        .fact-item {
          background: #F7F4EA;
          border: 1px solid #D9E2DE;
          border-radius: 6px;
          padding: 10px 12px;
        }
        .fact-lbl { font-size: 11px; font-weight: 600; color: #1B806F; }
        .fact-val { font-size: 13.5px; font-weight: 800; color: #126B62; margin-top: 2px; }
        .step-item {
          display: flex;
          gap: 10px;
          background: #FFFFFF;
          border: 1px solid #D9E2DE;
          border-radius: 6px;
          padding: 10px 12px;
          margin-bottom: 8px;
        }
        .step-num {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: #126B62;
          color: #FFFFFF;
          font-size: 11px;
          font-weight: 800;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .warning-box {
          margin-bottom: 20px;
          background: #FFFDF5;
          border: 1px solid #D6A52F;
          border-radius: 6px;
          padding: 12px 14px;
        }
        .next-steps-box {
          margin-bottom: 20px;
          background: #F7F4EA;
          border: 1px solid #D9E2DE;
          border-radius: 6px;
          padding: 12px 14px;
        }
        .footer-note {
          border-top: 1px solid #D9E2DE;
          padding-top: 12px;
          text-align: center;
          font-size: 10.5px;
          color: #1B806F;
          font-weight: 600;
          margin-top: 24px;
        }
        @media print {
          body { padding: 0; }
          .pdf-card { border: none; }
        }
      </style>
    </head>
    <body>
      <div class="pdf-card">
        <div class="header-row">
          <div>
            <h1 class="brand-name">SAHKAARSETU</h1>
            <p class="brand-sub">${labels.subTitle}</p>
          </div>
          <div class="domain-tag">${input.domainLabel}</div>
        </div>

        <div class="doc-banner">
          <h2>${labels.docTitle}</h2>
        </div>

        ${
          input.question
            ? `
          <div class="user-q-box">
            <div class="q-label">${labels.userQuestion}</div>
            <div class="q-text">"${input.question}"</div>
          </div>
        `
            : ""
        }

        ${
          input.summary
            ? `
          <div style="margin-bottom: 20px;">
            <div class="section-label">${labels.guidanceOverview}</div>
            <p style="font-size: 14px; line-height: 1.6; font-weight: 500; margin: 0;">${input.summary}</p>
            ${
              input.description
                ? `<p style="font-size: 13.5px; line-height: 1.6; margin-top: 8px;">${input.description}</p>`
                : ""
            }
          </div>
        `
            : ""
        }

        ${
          input.warnings && input.warnings.length > 0
            ? `
          <div class="warning-box">
            <div style="font-size: 11.5px; font-weight: 800; color: #D6A52F; text-transform: uppercase; margin-bottom: 6px;">${labels.warnings}</div>
            <ul style="margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.5;">
              ${input.warnings.map((w) => `<li>${w}</li>`).join("")}
            </ul>
          </div>
        `
            : ""
        }

        ${
          input.keyFacts && input.keyFacts.length > 0
            ? `
          <div style="margin-bottom: 20px;">
            <div class="section-label">${labels.keyFacts}</div>
            <div class="facts-grid">
              ${input.keyFacts
                .map(
                  (f) => `
                <div class="fact-item">
                  <div class="fact-lbl">${f.label}</div>
                  <div class="fact-val">${f.value}</div>
                </div>
              `
                )
                .join("")}
            </div>
          </div>
        `
            : ""
        }

        ${
          input.steps && input.steps.length > 0
            ? `
          <div style="margin-bottom: 20px;">
            <div class="section-label">${labels.steps}</div>
            <div>
              ${input.steps
                .map(
                  (st) => `
                <div class="step-item">
                  <div class="step-num">${st.stepNum}</div>
                  <div>
                    <div style="font-size: 13px; font-weight: 700;">${st.title}</div>
                    ${st.description ? `<div style="font-size: 12px; color: #555; margin-top: 2px;">${st.description}</div>` : ""}
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

        ${
          input.nextSteps && input.nextSteps.length > 0
            ? `
          <div class="next-steps-box">
            <div class="section-label" style="border: none;">${labels.nextSteps}</div>
            <ol style="margin: 0; padding-left: 20px; font-size: 13px; font-weight: 600; line-height: 1.6;">
              ${input.nextSteps.map((ns) => `<li style="margin-bottom: 4px;">${ns}</li>`).join("")}
            </ol>
          </div>
        `
            : ""
        }

        ${
          input.sources && input.sources.length > 0
            ? `
          <div style="margin-bottom: 20px;">
            <div class="section-label">${labels.sources}</div>
            <ul style="margin: 0; padding-left: 16px; font-size: 11.5px; color: #1B806F;">
              ${input.sources
                .map(
                  (s) =>
                    `<li><strong>${s.title}</strong>${s.authority ? ` (${s.authority})` : ""}</li>`
                )
                .join("")}
            </ul>
          </div>
        `
            : ""
        }

        <div class="footer-note">${labels.footer}</div>
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

  // Create printable Blob document window
  const blob = new Blob([htmlDoc], { type: "text/html" });
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
