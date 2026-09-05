/**
 * parseAnswer.ts
 *
 * Client-side parser for structured AI answer text.
 * The backend returns a plain `answer: string`. This parser detects
 * markdown-style section headers and splits the text into named sections
 * for richer rendering.
 *
 * No second AI call is made. Falls back to a single plain section if
 * no recognisable structure is found.
 */

export type SectionKind =
  | "DIRECT_ANSWER"
  | "WHAT_YOU_CAN_DO"
  | "IMPORTANT"
  | "NEXT_STEP"
  | "PLAIN";

export interface AnswerSection {
  kind: SectionKind;
  heading: string;
  body: string;
}

// Map of regex patterns → section kind
// Each pattern matches common heading variants produced by Gemini Flash
const SECTION_PATTERNS: Array<{ pattern: RegExp; kind: SectionKind; heading: string }> = [
  {
    pattern: /\*{0,2}(DIRECT ANSWER|थेट उत्तर|सीधा उत्तर)\*{0,2}:?/i,
    kind: "DIRECT_ANSWER",
    heading: "Direct Answer",
  },
  {
    pattern: /\*{0,2}(WHAT YOU CAN DO|तुम्ही काय करू शकता|आप क्या कर सकते हैं)\*{0,2}:?/i,
    kind: "WHAT_YOU_CAN_DO",
    heading: "What You Can Do",
  },
  {
    pattern: /\*{0,2}(IMPORTANT|महत्त्वाचे|महत्वपूर्ण)\*{0,2}:?/i,
    kind: "IMPORTANT",
    heading: "Important",
  },
  {
    pattern: /\*{0,2}(NEXT STEP|पुढील पाऊल|अगला कदम)\*{0,2}:?/i,
    kind: "NEXT_STEP",
    heading: "Next Step",
  },
];

/**
 * Split answer text into structured sections.
 * Returns an array of AnswerSection objects.
 * If no section markers found, returns a single PLAIN section.
 */
export function parseAnswer(text: string): AnswerSection[] {
  if (!text || !text.trim()) return [];

  // Build a combined regex to find any section header, preserving order
  const allPatterns = SECTION_PATTERNS.map((s) => s.pattern.source).join("|");
  const splitter = new RegExp(`(${allPatterns})`, "gi");

  const parts = text.split(splitter);

  if (parts.length <= 1) {
    // No structural markers — return as plain
    return [{ kind: "PLAIN", heading: "", body: text.trim() }];
  }

  const sections: AnswerSection[] = [];
  let currentKind: SectionKind = "PLAIN";
  let currentHeading = "";
  let bodyChunks: string[] = [];

  const flush = () => {
    const body = bodyChunks.join("").trim();
    if (body) {
      sections.push({ kind: currentKind, heading: currentHeading, body });
    }
    bodyChunks = [];
  };

  for (const part of parts) {
    if (!part) continue;

    // Check if this part is a section header
    let matched = false;
    for (const { pattern, kind, heading } of SECTION_PATTERNS) {
      if (pattern.test(part)) {
        flush();
        currentKind = kind;
        currentHeading = heading;
        matched = true;
        break;
      }
    }

    if (!matched) {
      bodyChunks.push(part);
    }
  }
  flush();

  // If first meaningful section was un-labelled intro text before first header,
  // keep it as a PLAIN prefix
  return sections.length > 0 ? sections : [{ kind: "PLAIN", heading: "", body: text.trim() }];
}

/**
 * Render a body string as bullet list items if lines start with - or •,
 * otherwise as plain paragraphs. Returns array of line strings.
 */
export function bodyToLines(body: string): string[] {
  return body
    .split("\n")
    .map((l) => l.replace(/^\*{1,2}(.*?)\*{1,2}$/, "$1").trim()) // strip bold markers
    .filter((l) => l.length > 0);
}
