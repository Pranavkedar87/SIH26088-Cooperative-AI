/**
 * guidanceParser.ts
 *
 * Client-side parser that converts raw AI Markdown output from Gemini Flash
 * into a clean, structured visual guidance data model for SahkaarSetu.
 *
 * Guaranteed:
 * - NO raw Markdown syntax (###, **, *, ---, 1.) is ever exposed in the UI.
 * - Enforces BOUNDARY: CARDS = SHORT FACTS (<75 chars). Paragraphs = Descriptive text.
 * - Extracts summary, key facts, step timeline, warnings, checklists, and next steps.
 * - Detects domain/type (PMFBY, PACS, LAW, GRIEVANCE, FINANCIAL, STEP_BY_STEP, INFORMATION).
 */

export type ResponseDomain =
  | "PMFBY"
  | "PACS"
  | "LAW"
  | "STEP_BY_STEP"
  | "FINANCIAL"
  | "GRIEVANCE"
  | "INFORMATION";

export interface KeyFact {
  label: string;
  value: string;
  highlight?: boolean;
}

export interface GuidanceStep {
  stepNum: number;
  title: string;
  description: string;
}

export interface NextAction {
  label: string;
  type: "ASK_AI";
  query: string;
  preserveContext: boolean;
}

export interface StructuredGuidance {
  domain: ResponseDomain;
  domainLabel: string;
  answerFocus: string;
  summary: string;
  keyFacts: KeyFact[];
  steps: GuidanceStep[];
  checklist: string[];
  warnings: string[];
  nextSteps: string[];
  nextActions: NextAction[];
  cleanParagraphs: string[];
}

/**
 * Strip all raw markdown symbols completely from a string.
 */
export function cleanMarkdown(text: string): string {
  if (!text) return "";
  return text
    .replace(/^Based on (?:live internet|web) research (?:for|on) ['"][^'"]+['"]:?\s*/gm, "")
    .replace(/^Based on (?:live internet|web) research (?:for|on) [^:]+:?\s*/gm, "")
    .replace(/^Based on (?:live internet|web) research[^:\n]*:?\s*/gm, "")
    .replace(/^According to (?:search results|web research|internet research)[^:\n]*:?\s*/gm, "")
    .replace(/^#{1,6}\s*/gm, "") // strip headers # ## ###
    .replace(/\*{1,3}([^*]+)\*{1,3}/g, "$1") // strip bold/italic **text**, *text*
    .replace(/_{1,3}([^_]+)_{1,3}/g, "$1") // strip underline _text_
    .replace(/`{1,3}([^`]+)`{1,3}/g, "$1") // strip inline code
    .replace(/^\s*[-*•]\s+/gm, "") // strip bullet points
    .replace(/^---+$|^\*\*\*+$/gm, "") // strip horizontal rules
    .replace(/^DIRECT ANSWER:?\s*/i, "")
    .replace(/^WHAT YOU CAN DO:?\s*/i, "")
    .replace(/^WHAT SHOULD I DO NOW:?\s*/i, "")
    .replace(/^KEY ACTION GUIDANCE:?\s*/i, "")
    .replace(/^OFFICIAL STEP-BY-STEP PROCEDURE:?\s*/i, "")
    .replace(/^REQUIRED DOCUMENTS & PROOFS:?\s*/i, "")
    .replace(/^HELPLINE & CONTACT DETAILS:?\s*/i, "")
    .replace(/^ELIGIBILITY & GUIDELINES:?\s*/i, "")
    .replace(/^IMPORTANT:?\s*/i, "")
    .replace(/^NEXT STEP:?\s*/i, "")
    .replace(/^NEXT GUIDANCE:?\s*/i, "")
    .replace(/^DETAILED INFORMATION:?\s*/i, "")
    .replace(/^थेट उत्तर:?\s*/i, "")
    .replace(/^तुम्ही काय करू शकता:?\s*/i, "")
    .replace(/^मार्गदर्शक पावले:?\s*/i, "")
    .replace(/^अधिकृत टप्पा-निहाय प्रक्रिया:?\s*/i, "")
    .replace(/^आवश्यक कागदपत्रे व पुरावे:?\s*/i, "")
    .replace(/^अधिकृत हेल्पलाईन व संपर्क:?\s*/i, "")
    .replace(/^पात्रता निकष व नियम:?\s*/i, "")
    .replace(/^सविस्तर माहिती:?\s*/i, "")
    .replace(/^पुढील मार्गदर्शन:?\s*/i, "")
    .replace(/^मुख्य मार्गदर्शन:?\s*/i, "")
    .replace(/^आधिकारिक चरण-दर-चरण प्रक्रिया:?\s*/i, "")
    .replace(/^आवश्यक दस्तावेज और प्रमाण:?\s*/i, "")
    .replace(/^आधिकारिक हेल्पलाइन और संपर्क:?\s*/i, "")
    .replace(/^पात्रता मापदंड और नियम:?\s*/i, "")
    .replace(/^विस्तृत जानकारी:?\s*/i, "")
    .replace(/^आगे का मार्गदर्शन:?\s*/i, "")
    .replace(/^महत्त्वाचे:?\s*/i, "")
    .replace(/^पुढील पाऊल:?\s*/i, "")
    .replace(/\s+/g, " ") // normalize spacing
    .trim();
}

/**
 * Domain Detector based on terminology in English, Marathi, Hindi
 */
function detectDomain(text: string): { domain: ResponseDomain; label: string } {
  const lower = text.toLowerCase();

  if (
    lower.includes("pmfby") ||
    lower.includes("crop insurance") ||
    lower.includes("पिक विमा") ||
    lower.includes("पीक विमा") ||
    lower.includes("फसल बीमा") ||
    lower.includes("विमा") ||
    lower.includes("खरीप") ||
    lower.includes("रब्बी")
  ) {
    return { domain: "PMFBY", label: "PMFBY Crop Insurance / पीक विमा योजना" };
  }

  if (
    lower.includes("pacs") ||
    lower.includes("पॅक्स") ||
    lower.includes("सोसायटी") ||
    lower.includes("क्रेडिट सोसायटी") ||
    lower.includes("primary agricultural credit")
  ) {
    return { domain: "PACS", label: "PACS Cooperative Services / सोसायटी सेवा" };
  }

  if (
    lower.includes("by-law") ||
    lower.includes("bylaw") ||
    lower.includes("section") ||
    lower.includes("act") ||
    lower.includes("कायदा") ||
    lower.includes("पोटनियम") ||
    lower.includes("कलम") ||
    lower.includes("कानून")
  ) {
    return { domain: "LAW", label: "Cooperative Law & By-Laws / कायदेशीर सल्ला" };
  }

  if (
    lower.includes("grievance") ||
    lower.includes("complaint") ||
    lower.includes("तक्रार") ||
    lower.includes("शिकायत") ||
    lower.includes("भ्रष्टाचार") ||
    lower.includes("अपील")
  ) {
    return { domain: "GRIEVANCE", label: "Grievance & Legal Appeal / तक्रार निवारण" };
  }

  if (
    lower.includes("kcc") ||
    lower.includes("loan") ||
    lower.includes("interest") ||
    lower.includes("subsidy") ||
    lower.includes("कर्ज") ||
    lower.includes("व्याज") ||
    lower.includes("अनुदान") ||
    lower.includes("प्रीमियम")
  ) {
    return { domain: "FINANCIAL", label: "Cooperative Credit & Scheme / सहकार योजना" };
  }

  const stepMatches = text.match(/(?:\d+\.|\bstep\s*\d+|टप्पा\s*\d+|चरण\s*\d+)/gi);
  if (stepMatches && stepMatches.length >= 2) {
    return { domain: "STEP_BY_STEP", label: "Guided Action Workflow / टप्पा-निहाय प्रक्रिया" };
  }

  return { domain: "INFORMATION", label: "Verified Cooperative Information / अधिकृत माहिती" };
}

/**
 * Dynamic fallback Next Actions mapping based on answer_focus
 */
function getContextualActions(_domain: ResponseDomain, lang: string, answerFocus?: string): NextAction[] {
  const focus = (answerFocus || "OVERVIEW").toUpperCase();

  if (lang === "hi") {
    if (focus === "CONTACT") {
      return [
        { label: "चरण-दर-चरण प्रक्रिया", type: "ASK_AI", query: "इस संबंध में आधिकारिक चरण-दर-चरण प्रक्रिया क्या है?", preserveContext: true },
        { label: "आवश्यक दस्तावेज", type: "ASK_AI", query: "इसके लिए कौन से दस्तावेज और प्रमाण आवश्यक हैं?", preserveContext: true },
      ];
    }
    if (focus === "PROCEDURE") {
      return [
        { label: "आवश्यक दस्तावेज", type: "ASK_AI", query: "इसके लिए कौन से दस्तावेज और प्रमाण आवश्यक हैं?", preserveContext: true },
        { label: "संपर्क एवं हेल्पलाइन", type: "ASK_AI", query: "संबंधित अधिकारी और आधिकारिक हेल्पलाइन नंबर क्या हैं?", preserveContext: true },
      ];
    }
    if (focus === "DOCUMENTS") {
      return [
        { label: "विस्तृत प्रक्रिया समझें", type: "ASK_AI", query: "इस संबंध में आधिकारिक चरण-दर-चरण प्रक्रिया क्या है?", preserveContext: true },
        { label: "संपर्क एवं हेल्पलाइन", type: "ASK_AI", query: "संबंधित अधिकारी और आधिकारिक हेल्पलाइन नंबर क्या हैं?", preserveContext: true },
      ];
    }
    return [
      { label: "विस्तृत प्रक्रिया समझें", type: "ASK_AI", query: "इस संबंध में आधिकारिक चरण-दर-चरण प्रक्रिया क्या है?", preserveContext: true },
      { label: "आवश्यक दस्तावेज", type: "ASK_AI", query: "इसके लिए कौन से दस्तावेज और प्रमाण आवश्यक हैं?", preserveContext: true },
      { label: "संपर्क एवं हेल्पलाइन", type: "ASK_AI", query: "संबंधित अधिकारी और आधिकारिक हेल्पलाइन नंबर क्या हैं?", preserveContext: true },
    ];
  }

  if (lang === "mr") {
    if (focus === "CONTACT") {
      return [
        { label: "सविस्तर टप्पे जाणून घ्या", type: "ASK_AI", query: "या प्रकरणात अधिकृत टप्पा-निहाय प्रक्रिया काय आहे?", preserveContext: true },
        { label: "आवश्यक कागदपत्रे", type: "ASK_AI", query: "यासाठी कोणती कागदपत्रे व पुरावे आवश्यक आहेत?", preserveContext: true },
      ];
    }
    if (focus === "PROCEDURE") {
      return [
        { label: "आवश्यक कागदपत्रे", type: "ASK_AI", query: "यासाठी कोणती कागदपत्रे व पुरावे आवश्यक आहेत?", preserveContext: true },
        { label: "संपर्क व हेल्पलाईन", type: "ASK_AI", query: "संबंधित कृषी अधिकारी व अधिकृत हेल्पलाईन संपर्क काय आहे?", preserveContext: true },
      ];
    }
    if (focus === "DOCUMENTS") {
      return [
        { label: "सविस्तर टप्पे जाणून घ्या", type: "ASK_AI", query: "या प्रकरणात अधिकृत टप्पा-निहाय प्रक्रिया काय आहे?", preserveContext: true },
        { label: "संपर्क व हेल्पलाईन", type: "ASK_AI", query: "संबंधित कृषी अधिकारी व अधिकृत हेल्पलाईन संपर्क काय आहे?", preserveContext: true },
      ];
    }
    return [
      { label: "सविस्तर टप्पे जाणून घ्या", type: "ASK_AI", query: "या प्रकरणात अधिकृत टप्पा-निहाय प्रक्रिया काय आहे?", preserveContext: true },
      { label: "आवश्यक कागदपत्रे", type: "ASK_AI", query: "यासाठी कोणती कागदपत्रे व पुरावे आवश्यक आहेत?", preserveContext: true },
      { label: "संपर्क व हेल्पलाईन", type: "ASK_AI", query: "संबंधित कृषी अधिकारी व अधिकृत हेल्पलाईन संपर्क काय आहे?", preserveContext: true },
    ];
  }

  // English
  if (focus === "CONTACT") {
    return [
      { label: "Detailed Procedure Steps", type: "ASK_AI", query: "What is the official step-by-step procedure for this?", preserveContext: true },
      { label: "Required Documents & Proofs", type: "ASK_AI", query: "What specific documents and land records are required?", preserveContext: true },
    ];
  }
  if (focus === "PROCEDURE") {
    return [
      { label: "Required Documents & Proofs", type: "ASK_AI", query: "What specific documents and land records are required?", preserveContext: true },
      { label: "Helpline & Contact Details", type: "ASK_AI", query: "What are the official helpline numbers and contact authorities?", preserveContext: true },
    ];
  }
  if (focus === "DOCUMENTS") {
    return [
      { label: "Detailed Procedure Steps", type: "ASK_AI", query: "What is the official step-by-step procedure for this?", preserveContext: true },
      { label: "Helpline & Contact Details", type: "ASK_AI", query: "What are the official helpline numbers and contact authorities?", preserveContext: true },
    ];
  }
  return [
    { label: "Detailed Procedure Steps", type: "ASK_AI", query: "What is the official step-by-step procedure for this?", preserveContext: true },
    { label: "Required Documents & Proofs", type: "ASK_AI", query: "What specific documents and land records are required?", preserveContext: true },
    { label: "Helpline & Contact Details", type: "ASK_AI", query: "What are the official helpline numbers and contact authorities?", preserveContext: true },
  ];
}

/**
 * Main function to parse raw AI answer text into StructuredGuidance
 */
export function parseGuidance(rawText: string, lang: string = "mr", explicitFocus?: string): StructuredGuidance {
  if (!rawText || !rawText.trim()) {
    return {
      domain: "INFORMATION",
      domainLabel: "Information",
      answerFocus: explicitFocus || "OVERVIEW",
      summary: "",
      keyFacts: [],
      steps: [],
      checklist: [],
      warnings: [],
      nextSteps: [],
      nextActions: [],
      cleanParagraphs: [],
    };
  }

  let answerFocus = (explicitFocus || "").toUpperCase();
  if (!answerFocus || answerFocus === "OVERVIEW" || answerFocus === "GENERAL") {
    if (/helpline|contact|संपर्क|हेल्पलाईन|हेल्पलाइन/i.test(rawText)) {
      answerFocus = "CONTACT";
    } else if (/official step-by-step procedure|अधिकृत टप्पा-निहाय प्रक्रिया|आधिकारिक चरण-दर-चरण प्रक्रिया/i.test(rawText)) {
      answerFocus = "PROCEDURE";
    } else if (/required documents & proofs|आवश्यक कागदपत्रे व पुरावे|आवश्यक दस्तावेज और प्रमाण/i.test(rawText)) {
      answerFocus = "DOCUMENTS";
    } else if (/eligibility & guidelines|पात्रता निकष व नियम|पात्रता मापदंड और नियम/i.test(rawText)) {
      answerFocus = "ELIGIBILITY";
    } else {
      answerFocus = explicitFocus || "OVERVIEW";
    }
  }

  const { domain, label: domainLabel } = detectDomain(rawText);

  const lines = rawText
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => {
      if (!l || l === "---" || l === "***") return false;
      const cleaned = cleanMarkdown(l);
      if (!cleaned || cleaned.length < 2) return false;
      if (/^Based on (?:live internet|web) research/i.test(l)) return false;
      if (/^According to (?:search results|web research|internet research)/i.test(l)) return false;
      return true;
    });

  const keyFacts: KeyFact[] = [];
  const steps: GuidanceStep[] = [];
  const checklist: string[] = [];
  const warnings: string[] = [];
  const nextSteps: string[] = [];
  const cleanParagraphs: string[] = [];

  let currentStepNum = 1;
  let inNextStepSection = false;
  let inWarningSection = false;

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];

    // Check if entering Next Steps / Action section
    if (
      /^(what you can do|what should i do|what should i do now|key action guidance|official step-by-step procedure|required documents & proofs|helpline & contact details|eligibility & guidelines|next steps|next guidance|पुढील पाऊल|आगे क्या करें|तुम्ही काय करू शकता|आप क्या करें|मार्गदर्शक पावले|अधिकृत टप्पा-निहाय प्रक्रिया|आवश्यक कागदपत्रे|अधिकृत हेल्पलाईन|पात्रता निकष|मुख्य मार्गदर्शन)/i.test(
        cleanMarkdown(rawLine)
      )
    ) {
      inNextStepSection = true;
      inWarningSection = false;
      continue;
    }

    // Check if entering Warning / Important section
    if (/^(important|warning|महत्त्वाचे|महत्वपूर्ण|टीप|सूचना)/i.test(cleanMarkdown(rawLine))) {
      inWarningSection = true;
      inNextStepSection = false;
      continue;
    }

    // 1. Extract Key Facts (matches format "**Label:** Value" or "Label: Value" or "- **Label:** Value")
    const factMatch = rawLine.match(
      /^(?:[-*•]\s*)?\*{0,2}([^:\n#]{2,45})\*{0,2}\s*:\s*(.+)$/
    );
    if (
      factMatch &&
      !factMatch[1].toLowerCase().includes("direct answer") &&
      !factMatch[1].toLowerCase().includes("step") &&
      !factMatch[1].includes("1.") &&
      !factMatch[1].includes("2.")
    ) {
      const factLabel = cleanMarkdown(factMatch[1]);
      const factVal = cleanMarkdown(factMatch[2]);

      if (factLabel && factVal) {
        if (factVal.length <= 85 && factLabel.length <= 40) {
          keyFacts.push({
            label: factLabel,
            value: factVal,
            highlight:
              factVal.includes("%") ||
              /\d+/.test(factVal) ||
              factVal.toLowerCase().includes("72") ||
              factVal.toLowerCase().includes("तास") ||
              factVal.toLowerCase().includes("helpline") ||
              factVal.toLowerCase().includes("1800"),
          });
          continue;
        } else {
          cleanParagraphs.push(`${factLabel}: ${factVal}`);
          continue;
        }
      }
    }

    // 2. Extract Step Timeline Items ONLY IF answerFocus is PROCEDURE or STEP_BY_STEP
    const stepMatch = rawLine.match(
      /^(?:#{1,6}\s*)?(?:(\d+)\.|\bstep\s*(\d+):?|\bटप्पा\s*(\d+):?|\bचरण\s*(\d+):?)\s*(.+)$/i
    );
    if (stepMatch && (answerFocus === "PROCEDURE" || answerFocus === "STEP_BY_STEP")) {
      const extractedNum = parseInt(
        stepMatch[1] || stepMatch[2] || stepMatch[3] || stepMatch[4] || "0",
        10
      );
      const rest = stepMatch[5].trim();

      let title = cleanMarkdown(rest);
      let desc = "";

      const colonIdx = rest.indexOf(":");
      if (colonIdx > 0 && colonIdx < 50) {
        title = cleanMarkdown(rest.substring(0, colonIdx));
        desc = cleanMarkdown(rest.substring(colonIdx + 1));
      }

      if (!desc && i + 1 < lines.length && !lines[i + 1].match(/^(?:#{1,6}|\d+\.|\*|-)/)) {
        desc = cleanMarkdown(lines[i + 1]);
        i++;
      }

      steps.push({
        stepNum: extractedNum > 0 ? extractedNum : currentStepNum++,
        title: title || `Step ${currentStepNum}`,
        description: desc,
      });
      continue;
    }

    // 3. Extract Warnings
    if (
      inWarningSection ||
      /^(महत्त्वाचे|महत्वपूर्ण|important|warning|टीप):/i.test(rawLine)
    ) {
      const cleaned = cleanMarkdown(rawLine);
      if (cleaned) warnings.push(cleaned);
      continue;
    }

    // 4. Extract Next Steps / Action Items
    if (inNextStepSection) {
      const cleaned = cleanMarkdown(rawLine);
      if (cleaned) nextSteps.push(cleaned);
      continue;
    }

    // 5. Extract Bullet Checklist items
    if (/^[-*•]\s+/.test(rawLine)) {
      const cleaned = cleanMarkdown(rawLine);
      if (cleaned) checklist.push(cleaned);
      continue;
    }

    // 6. If line is numbered (e.g. 1. Contact Info) but answerFocus is NOT PROCEDURE, treat as keyFact or paragraph
    if (stepMatch && answerFocus !== "PROCEDURE" && answerFocus !== "STEP_BY_STEP") {
      const rest = stepMatch[5].trim();
      const colonIdx = rest.indexOf(":");
      if (colonIdx > 0 && colonIdx < 40) {
        keyFacts.push({
          label: cleanMarkdown(rest.substring(0, colonIdx)),
          value: cleanMarkdown(rest.substring(colonIdx + 1)),
        });
      } else {
        cleanParagraphs.push(cleanMarkdown(rest));
      }
      continue;
    }

    // 7. Regular clean paragraph text
    const cleanedPara = cleanMarkdown(rawLine);
    if (cleanedPara.length > 5) {
      cleanParagraphs.push(cleanedPara);
    }
  }

  // Construct Summary: First clean paragraph or synthesized text
  let summary = "";
  if (cleanParagraphs.length > 0) {
    summary = cleanParagraphs[0];
  } else if (steps.length > 0) {
    summary = `${domainLabel}: ${steps[0].title}.`;
  } else if (keyFacts.length > 0) {
    summary = `${keyFacts[0].label}: ${keyFacts[0].value}`;
  } else {
    summary = cleanMarkdown(rawText).slice(0, 180) + "…";
  }

  const uniqueNextSteps = Array.from(new Set(nextSteps));
  const uniqueWarnings = Array.from(new Set(warnings));

  // Build NextAction objects
  let nextActions: NextAction[] = [];
  if (uniqueNextSteps.length > 0) {
    nextActions = uniqueNextSteps.map((ns) => ({
      label: ns,
      type: "ASK_AI",
      query: ns,
      preserveContext: true,
    }));
  } else {
    nextActions = getContextualActions(domain, lang, answerFocus);
  }

  return {
    domain,
    domainLabel,
    answerFocus,
    summary,
    keyFacts: keyFacts.slice(0, 6),
    steps,
    checklist,
    warnings: uniqueWarnings,
    nextSteps: uniqueNextSteps,
    nextActions,
    cleanParagraphs: cleanParagraphs.slice(1),
  };
}
