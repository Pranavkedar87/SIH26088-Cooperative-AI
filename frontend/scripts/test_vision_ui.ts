/**
 * Phase 3C.4 — Document Analysis & Confirmation UI Test Suite
 *
 * 20 required test groups:
 *   1.  DocumentAnalysisModal exists
 *   2.  VisionAnalyzeResponse consumed
 *   3.  document type rendered & mapped
 *   4.  readability rendered
 *   5.  summary rendered & labeled as AI interpretation
 *   6.  key fields rendered
 *   7.  PII notice rendered
 *   8.  identity document refusal
 *   9.  suggested question chips rendered
 *   10. custom question field
 *   11. question returned to parent
 *   12. no /api/query call from modal
 *   13. retake action
 *   14. mobile modal styles
 *   15. accessibility attributes
 *   16. EN localization
 *   17. HI localization
 *   18. MR localization
 *   19. no raw PII unmasking
 *   20. no localStorage image persistence
 *
 * Run: node --experimental-strip-types frontend/scripts/test_vision_ui.ts
 */

import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, resolve } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const root = resolve(__dirname, "../..");

const passed: string[] = [];
const failed: string[] = [];

function assert(condition: boolean, name: string, detail?: string): void {
  if (condition) {
    passed.push(name);
    console.log(`  ✓ ${name}`);
  } else {
    failed.push(name);
    console.error(`  ✗ ${name}${detail ? ` — ${detail}` : ""}`);
  }
}

function src(relPath: string): string {
  return readFileSync(resolve(root, relPath), "utf8");
}

console.log("================================================================================");
console.log("CITIZEN PHASE 3C.4: DOCUMENT ANALYSIS & CONFIRMATION UI TEST SUITE");
console.log("================================================================================");

// ─────────────────────────────────────────────────────────────────────────────
// 1. DocumentAnalysisModal exists
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[1] DocumentAnalysisModal component file exists");
{
  let modalContent = "";
  try {
    modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  } catch {
    assert(false, "DocumentAnalysisModal.tsx is readable");
  }
  assert(modalContent.length > 0, "DocumentAnalysisModal.tsx exists and is non-empty");
  assert(
    modalContent.includes("export const DocumentAnalysisModal"),
    "DocumentAnalysisModal component is exported"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. VisionAnalyzeResponse consumed
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[2] VisionAnalyzeResponse consumed by DocumentAnalysisModal");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  assert(
    modalContent.includes("VisionAnalyzeResponse"),
    "imports and types result prop as VisionAnalyzeResponse"
  );
  assert(
    modalContent.includes("result: VisionAnalyzeResponse"),
    "Props interface requires result: VisionAnalyzeResponse"
  );
  assert(
    modalContent.includes("result.document_type") &&
    modalContent.includes("result.readability") &&
    modalContent.includes("result.key_fields"),
    "consumes document_type, readability, and key_fields from result"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. Document type rendered & mapped
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[3] Document type rendered with friendly localized mapping");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  const en = src("frontend/src/i18n/locales/en.ts");

  assert(
    modalContent.includes("getDocTypeLabel"),
    "helper function getDocTypeLabel maps document types"
  );
  assert(
    en.includes('"docAnalysis.type.PMFBY_POLICY"') &&
    en.includes('"docAnalysis.type.LAND_RECORD_7_12"') &&
    en.includes('"docAnalysis.type.COOPERATIVE_NOTICE"') &&
    en.includes('"docAnalysis.type.PACS_MEMBERSHIP_FORM"') &&
    en.includes('"docAnalysis.type.SUBSIDY_LETTER"') &&
    en.includes('"docAnalysis.type.FERTILIZER_RECEIPT"') &&
    en.includes('"docAnalysis.type.LOAN_PASSBOOK"') &&
    en.includes('"docAnalysis.type.IDENTITY_DOCUMENT"') &&
    en.includes('"docAnalysis.type.UNKNOWN"'),
    "all DocumentType union members mapped in locale"
  );
  assert(
    modalContent.includes("docAnalysis.identified"),
    "displays Document Identified label"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. Readability rendered
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[4] Readability status rendered with retake prompt when not CLEAR");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  const en = src("frontend/src/i18n/locales/en.ts");

  assert(
    modalContent.includes("getReadabilityLabel"),
    "getReadabilityLabel maps readability enum to localized string"
  );
  assert(
    en.includes('"docAnalysis.readability.CLEAR"') &&
    en.includes('"docAnalysis.readability.BLURRY"') &&
    en.includes('"docAnalysis.readability.CROPPED"') &&
    en.includes('"docAnalysis.readability.POOR_LIGHTING"'),
    "all 4 ReadabilityStatus values localized"
  );
  assert(
    modalContent.includes("!isClear") &&
    modalContent.includes("docAnalysis.retakeWarning"),
    "renders retake warning and button if readability is not CLEAR"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. Document summary rendered & labeled as AI interpretation
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[5] Document summary rendered and clearly labeled as AI interpretation");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  const en = src("frontend/src/i18n/locales/en.ts");

  assert(
    modalContent.includes("result.document_summary"),
    "renders result.document_summary conditionally"
  );
  assert(
    modalContent.includes("docAnalysis.summaryTitle"),
    "displays summary title"
  );
  assert(
    modalContent.includes("docAnalysis.summaryDisclaimer"),
    "displays explicit disclaimer that summary is AI interpretation"
  );
  assert(
    en.includes("not an official government certification"),
    "disclaimer explicitly notes it is not government certification"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. Extracted key fields rendered
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[6] Extracted key fields rendered in responsive table");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  assert(
    modalContent.includes("Object.entries(result.key_fields)"),
    "iterates over key_fields entries"
  );
  assert(
    modalContent.includes("doc-analysis-fields-table"),
    "uses dedicated fields table container"
  );
  assert(
    modalContent.includes("docAnalysis.keyFieldsTitle"),
    "displays Key Extracted Details header"
  );
  assert(
    modalContent.includes("docAnalysis.referenceNotice"),
    "shows Reference information only disclaimer"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. Sensitive PII notice rendered
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[7] Sensitive PII notice rendered conditionally");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  assert(
    modalContent.includes("result.has_sensitive_pii"),
    "checks result.has_sensitive_pii before rendering banner"
  );
  assert(
    modalContent.includes("docAnalysis.piiNotice"),
    "renders gentle PII masking notice"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 8. Identity document refusal
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[8] Identity document refusal guard");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  assert(
    modalContent.includes('isIdentity ? (') || modalContent.includes('result.document_type === "IDENTITY_DOCUMENT"'),
    "checks for IDENTITY_DOCUMENT"
  );
  assert(
    modalContent.includes("doc-analysis-refusal-card"),
    "renders specialized refusal card for identity documents"
  );
  assert(
    modalContent.includes("docAnalysis.scanAnother"),
    "provides Scan Another Document action on refusal"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 9. Suggested question chips rendered
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[9] Suggested question chips rendered as touch-friendly buttons");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  assert(
    modalContent.includes("result.suggested_questions.map"),
    "maps suggested questions to buttons"
  );
  assert(
    modalContent.includes("doc-analysis-chip"),
    "applies chip styling class"
  );
  assert(
    modalContent.includes("handleChipClick"),
    "wires chip click to handler"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 10. Custom question input field
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[10] Custom question input form");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  assert(
    modalContent.includes("<form") && modalContent.includes("handleCustomSubmit"),
    "renders form with custom question submit handler"
  );
  assert(
    modalContent.includes("docAnalysis.customQuestionPlaceholder"),
    "provides placeholder for user input"
  );
  assert(
    modalContent.includes("disabled={!customQuestion.trim()}"),
    "disables submit button when input is empty"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 11. Question returned to parent
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[11] Question returned to parent via onSelectQuestion callback");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  const navContent = src("frontend/src/components/Navigation.tsx");
  const chatContent = src("frontend/src/components/ChatInput.tsx");

  assert(
    modalContent.includes("onSelectQuestion: (question: string) => void"),
    "modal defines onSelectQuestion prop"
  );
  assert(
    modalContent.includes("onSelectQuestion(trimmed)") &&
    modalContent.includes("onSelectQuestion(question)"),
    "calls onSelectQuestion with chosen question"
  );
  assert(
    navContent.includes("onSelectQuestion={"),
    "Navigation wires onSelectQuestion prop"
  );
  assert(
    chatContent.includes("onSelectQuestion={"),
    "ChatInput wires onSelectQuestion prop"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 12. No /api/query call from DocumentAnalysisModal
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[12] DocumentAnalysisModal does NOT make network calls (no /api/query)");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  assert(
    !modalContent.includes("/api/query"),
    "modal does NOT contain /api/query"
  );
  assert(
    !modalContent.includes("sendQuery"),
    "modal does NOT import or call sendQuery"
  );
  assert(
    !modalContent.includes("fetch("),
    "modal does NOT call fetch directly"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 13. Retake action
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[13] Retake action available and wired to parent");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  const navContent = src("frontend/src/components/Navigation.tsx");
  const chatContent = src("frontend/src/components/ChatInput.tsx");

  assert(
    modalContent.includes("onRetake: () => void"),
    "modal defines onRetake prop"
  );
  assert(
    navContent.includes('setActiveCameraMode("document_scan")'),
    "Navigation reopens camera on retake"
  );
  assert(
    chatContent.includes('setActiveCameraMode("document_scan")'),
    "ChatInput reopens camera on retake"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 14. Mobile modal styles
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[14] Mobile responsive CSS styles for DocumentAnalysisModal");
{
  const css = src("frontend/src/App.css");
  assert(
    css.includes(".doc-analysis-backdrop") &&
    css.includes(".doc-analysis-card"),
    "backdrop and card classes defined in App.css"
  );
  assert(
    css.includes("@media (max-width: 480px)") &&
    css.includes(".doc-analysis-card"),
    "media query includes mobile adaptations for analysis card"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 15. Accessibility attributes
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[15] Accessibility attributes on DocumentAnalysisModal");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  assert(
    modalContent.includes('role="dialog"') &&
    modalContent.includes('aria-modal="true"'),
    "dialog semantics role=dialog and aria-modal=true present"
  );
  assert(
    modalContent.includes('aria-labelledby="doc-analysis-title"'),
    "aria-labelledby associates modal with its title"
  );
  assert(
    modalContent.includes("Escape"),
    "keyboard ESC listener attached to close modal"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 16. EN localization completeness
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[16] English localization strings complete");
{
  const en = src("frontend/src/i18n/locales/en.ts");
  const requiredKeys = [
    "docAnalysis.title",
    "docAnalysis.identified",
    "docAnalysis.summaryTitle",
    "docAnalysis.keyFieldsTitle",
    "docAnalysis.questionsTitle",
    "docAnalysis.customQuestionTitle",
    "docAnalysis.askButton",
    "docAnalysis.scanAnother",
    "docAnalysis.retake",
    "docAnalysis.close",
  ];
  for (const k of requiredKeys) {
    assert(en.includes(`"${k}"`), `en.ts includes ${k}`);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 17. HI localization completeness
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[17] Hindi localization strings complete");
{
  const hi = src("frontend/src/i18n/locales/hi.ts");
  const requiredKeys = [
    "docAnalysis.title",
    "docAnalysis.identified",
    "docAnalysis.summaryTitle",
    "docAnalysis.keyFieldsTitle",
    "docAnalysis.questionsTitle",
    "docAnalysis.customQuestionTitle",
    "docAnalysis.askButton",
    "docAnalysis.scanAnother",
    "docAnalysis.retake",
    "docAnalysis.close",
  ];
  for (const k of requiredKeys) {
    assert(hi.includes(`"${k}"`), `hi.ts includes ${k}`);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 18. MR localization completeness
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[18] Marathi localization strings complete");
{
  const mr = src("frontend/src/i18n/locales/mr.ts");
  const requiredKeys = [
    "docAnalysis.title",
    "docAnalysis.identified",
    "docAnalysis.summaryTitle",
    "docAnalysis.keyFieldsTitle",
    "docAnalysis.questionsTitle",
    "docAnalysis.customQuestionTitle",
    "docAnalysis.askButton",
    "docAnalysis.scanAnother",
    "docAnalysis.retake",
    "docAnalysis.close",
  ];
  for (const k of requiredKeys) {
    assert(mr.includes(`"${k}"`), `mr.ts includes ${k}`);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 19. No raw PII unmasking client-side
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[19] No raw PII unmasking in DocumentAnalysisModal");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  assert(
    !modalContent.includes("unmask") &&
    !modalContent.includes("decodePII"),
    "no client-side PII unmasking functions"
  );
  assert(
    modalContent.includes("val ? String(val) : \"—\""),
    "renders values as provided from backend directly"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 20. No localStorage image persistence
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[20] No localStorage image persistence");
{
  const modalContent = src("frontend/src/components/DocumentAnalysisModal.tsx");
  const navContent = src("frontend/src/components/Navigation.tsx");
  const chatContent = src("frontend/src/components/ChatInput.tsx");

  assert(
    !modalContent.includes("localStorage"),
    "modal does NOT touch localStorage"
  );
  assert(
    !navContent.includes("localStorage.setItem") || !navContent.includes("image"),
    "Navigation does NOT save images to localStorage"
  );
  assert(
    !chatContent.includes("localStorage.setItem") || !chatContent.includes("image"),
    "ChatInput does NOT save images to localStorage"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Summary
// ─────────────────────────────────────────────────────────────────────────────
const total = passed.length + failed.length;
console.log(`\n${"─".repeat(80)}`);
console.log(`RESULTS: ${passed.length}/${total} CHECKS PASSED`);
console.log(`${"─".repeat(80)}`);

if (failed.length > 0) {
  console.error(`\nFAILED CHECKS (${failed.length}):`);
  failed.forEach((f) => console.error(`  ✗ ${f}`));
  console.log("\nFINAL VERDICT: BLOCKED — DOCUMENT ANALYSIS UI NOT SAFE");
  process.exit(1);
} else {
  console.log("\nFINAL VERDICT: PASS — DOCUMENT ANALYSIS UI VERIFIED");
  process.exit(0);
}
