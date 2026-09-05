/**
 * guidanceParser.ts
 *
 * Client-side parser that converts raw AI Markdown output from Gemini Flash
 * into a clean, structured visual guidance data model for SahkaarSetu.
 *
 * Guaranteed:
 * - NO raw Markdown syntax (###, **, *, ---, 1.) is ever exposed in the UI.
 * - Extracts summary, key facts/metrics, step timeline, warnings, checklists, and next steps.
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

export interface StructuredGuidance {
  domain: ResponseDomain;
  domainLabel: string;
  summary: string;
  keyFacts: KeyFact[];
  steps: GuidanceStep[];
  checklist: string[];
  warnings: string[];
  nextSteps: string[];
  cleanParagraphs: string[];
}

/**
 * Strip all raw markdown symbols from a string.
 */
export function cleanMarkdown(text: string): string {
  if (!text) return "";
  return text
    .replace(/^#{1,6}\s*/gm, "") // strip headers # ## ###
    .replace(/\*{1,3}([^*]+)\*{1,3}/g, "$1") // strip bold/italic **text**, *text*
    .replace(/_{1,3}([^_]+)_{1,3}/g, "$1") // strip underline _text_
    .replace(/`{1,3}([^`]+)`{1,3}/g, "$1") // strip inline code
    .replace(/^\s*[-*•]\s+/gm, "") // strip bullet points
    .replace(/^---+$|^\*\*\*+$/gm, "") // strip horizontal rules
    .replace(/^DIRECT ANSWER:?\s*/i, "")
    .replace(/^WHAT YOU CAN DO:?\s*/i, "")
    .replace(/^IMPORTANT:?\s*/i, "")
    .replace(/^NEXT STEP:?\s*/i, "")
    .replace(/^थेट उत्तर:?\s*/i, "")
    .replace(/^तुम्ही काय करू शकता:?\s*/i, "")
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

  // Count step occurrences
  const stepMatches = text.match(/(?:\d+\.|\bstep\s*\d+|टप्पा\s*\d+|चरण\s*\d+)/gi);
  if (stepMatches && stepMatches.length >= 2) {
    return { domain: "STEP_BY_STEP", label: "Guided Action Workflow / टप्पा-निहाय प्रक्रिया" };
  }

  return { domain: "INFORMATION", label: "Verified Cooperative Information / अधिकृत माहिती" };
}

/**
 * Main function to parse raw AI answer text into StructuredGuidance
 */
export function parseGuidance(rawText: string, _lang: string = "mr"): StructuredGuidance {
  if (!rawText || !rawText.trim()) {
    return {
      domain: "INFORMATION",
      domainLabel: "Information",
      summary: "",
      keyFacts: [],
      steps: [],
      checklist: [],
      warnings: [],
      nextSteps: [],
      cleanParagraphs: [],
    };
  }

  const { domain, label: domainLabel } = detectDomain(rawText);

  const lines = rawText
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.length > 0 && l !== "---" && l !== "***");

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
      /^(what you can do|next steps|पुढील पाऊल|आगे क्या करें|तुम्ही काय करू शकता)/i.test(
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
      if (factLabel && factVal && factLabel.length <= 40) {
        keyFacts.push({
          label: factLabel,
          value: factVal,
          highlight:
            factVal.includes("%") ||
            /\d+/.test(factVal) ||
            factVal.toLowerCase().includes("72") ||
            factVal.toLowerCase().includes("तास"),
        });
        continue;
      }
    }

    // 2. Extract Step Timeline Items
    // Format: "1. **Title:** Desc" or "### 1. Title" or "1. Title: Desc" or "Step 1: Title"
    const stepMatch = rawLine.match(
      /^(?:#{1,6}\s*)?(?:(\d+)\.|\bstep\s*(\d+):?|\bटप्पा\s*(\d+):?|\bचरण\s*(\d+):?)\s*(.+)$/i
    );
    if (stepMatch) {
      const extractedNum = parseInt(
        stepMatch[1] || stepMatch[2] || stepMatch[3] || stepMatch[4] || "0",
        10
      );
      const rest = stepMatch[5].trim();

      // Split rest into Title vs Desc if colon exists
      let title = cleanMarkdown(rest);
      let desc = "";

      const colonIdx = rest.indexOf(":");
      if (colonIdx > 0 && colonIdx < 50) {
        title = cleanMarkdown(rest.substring(0, colonIdx));
        desc = cleanMarkdown(rest.substring(colonIdx + 1));
      }

      // Check if next line is description for this step
      if (!desc && i + 1 < lines.length && !lines[i + 1].match(/^(?:#{1,6}|\d+\.|\*|-)/)) {
        desc = cleanMarkdown(lines[i + 1]);
        i++; // consume next line
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

    // 6. Regular clean paragraph text
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

  // Deduplicate and trim arrays
  const uniqueNextSteps = Array.from(new Set(nextSteps));
  const uniqueWarnings = Array.from(new Set(warnings));

  return {
    domain,
    domainLabel,
    summary,
    keyFacts: keyFacts.slice(0, 6), // limit to max 6 key fact cards
    steps,
    checklist,
    warnings: uniqueWarnings,
    nextSteps: uniqueNextSteps,
    cleanParagraphs: cleanParagraphs.slice(1), // rest of paragraphs
  };
}
