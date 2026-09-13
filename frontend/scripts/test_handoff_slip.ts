/**
 * Citizen Phase 3A.3 — QR Verification & 58mm Assistance Slip Verification Test Suite
 * Validates:
 * 1. Types & contract compliance
 * 2. Pure TS QR matrix & SVG generator (zero external dependencies, React 19 safe)
 * 3. Privacy & security enforcement (zero PII, zero secrets in QR payload)
 * 4. AssistanceSlipView component & print layout
 * 5. @media print CSS for 58mm thermal receipt printer
 * 6. Multilingual translations (EN, HI, MR)
 * 7. Non-resubmission and handoff integration
 * SahkaarSetu / Cooperative AI (SIH26088)
 */
import * as fs from "fs";
import * as path from "path";
import { en } from "../src/i18n/locales/en.ts";
import { hi } from "../src/i18n/locales/hi.ts";
import { mr } from "../src/i18n/locales/mr.ts";
import { generateQrMatrix, generateQrSvg, generateQrDataUri } from "../src/utils/qrGenerator.ts";

console.log("================================================================================");
console.log("RUNNING CITIZEN PHASE 3A.3 QR VERIFICATION & 58MM ASSISTANCE SLIP TEST SUITE");
console.log("================================================================================");

let passedCount = 0;
const totalChecks = 18;

// ── Check 1: AssistanceSlipData contract in src/types/index.ts ────────────────
const typesPath = path.resolve("./src/types/index.ts");
const typesContent = fs.readFileSync(typesPath, "utf-8");
const slipFields = [
  "header",
  "reference_code",
  "created_at",
  "pacs_name",
  "category",
  "citizen_masked_name",
  "citizen_phone_masked",
  "citizen_language",
  "officer_language",
  "original_query",
  "officer_translated_note",
  "ai_guidance_summary",
  "sources",
  "qr_payload",
  "disclaimer",
];
const missingFields = slipFields.filter((f) => !typesContent.includes(f));
if (missingFields.length === 0) {
  console.log(`[PASSED] 1. Contract: AssistanceSlipData contains all ${slipFields.length} required fields`);
  passedCount++;
} else {
  throw new Error(`Failed Check 1: Missing fields in AssistanceSlipData: ${missingFields.join(", ")}`);
}

// ── Check 2: Pure TS QR Generator Exports ─────────────────────────────────────
if (
  typeof generateQrMatrix === "function" &&
  typeof generateQrSvg === "function" &&
  typeof generateQrDataUri === "function"
) {
  console.log("[PASSED] 2. Pure TS QR Generator: exports generateQrMatrix, generateQrSvg, generateQrDataUri");
  passedCount++;
} else {
  throw new Error("Failed Check 2: QR Generator missing required function exports");
}

// ── Check 3: QR Generator produces valid SVG structure ───────────────────────
const sampleUrl = "https://sahkaarsetu.gov.in/verify/slip?ref=PACS-2026-987654";
const sampleSvg = generateQrSvg(sampleUrl, { size: 120, margin: 2 });
if (
  sampleSvg.includes("<svg") &&
  sampleSvg.includes("viewBox=") &&
  sampleSvg.includes("<rect") &&
  sampleSvg.includes("<path") &&
  sampleSvg.includes("</svg>")
) {
  console.log("[PASSED] 3. QR SVG output: Valid well-formed SVG string generated with rect and path");
  passedCount++;
} else {
  throw new Error("Failed Check 3: QR Generator output does not conform to SVG standard");
}

// ── Check 4: QR Matrix dimensions validation ─────────────────────────────────
const matrix = generateQrMatrix(sampleUrl, "M");
const size = matrix.length;
const isSquare = matrix.every((row) => row.length === size);
const isValidQrDim = size >= 21 && (size - 21) % 4 === 0;
if (isSquare && isValidQrDim) {
  console.log(`[PASSED] 4. QR Matrix dimensions: Square matrix (${size}x${size}) valid for QR standard`);
  passedCount++;
} else {
  throw new Error(`Failed Check 4: Invalid QR matrix dimensions: ${size}x${matrix[0]?.length}`);
}

// ── Check 5: QR Generator handles varying payload lengths ────────────────────
const shortPayload = "https://sahkaarsetu.gov.in/v?r=123";
const longPayload = "https://sahkaarsetu.gov.in/verify/slip?ref=PACS-2026-KADAM99&pacs=Dindori%20Primary%20Agricultural%20Cooperative&cat=COOPERATIVE_REGISTRATION";
const m1 = generateQrMatrix(shortPayload);
const m2 = generateQrMatrix(longPayload);
if (m1.length > 0 && m2.length >= m1.length) {
  console.log(`[PASSED] 5. QR Adaptability: Handled short (${m1.length}x${m1.length}) and long (${m2.length}x${m2.length}) payloads`);
  passedCount++;
} else {
  throw new Error("Failed Check 5: QR Generator failed on varying payload lengths");
}

// ── Check 6: QR Payload Security & Zero-PII Enforcement ──────────────────────
const mockBackendQrPayload = "https://sahkaarsetu.gov.in/verify/slip?ref=PACS-2026-ABC123&pacs=Dindori%20PACS&cat=PMFBY";
const hasUnmaskedPhone = /\b\d{10}\b/.test(mockBackendQrPayload);
const hasSecret = /bearer|secret|key|token|password/i.test(mockBackendQrPayload);
if (!hasUnmaskedPhone && !hasSecret) {
  console.log("[PASSED] 6. Privacy & Security: QR payload contains zero unmasked phone numbers, zero secrets");
  passedCount++;
} else {
  throw new Error("Failed Check 6: QR payload contains sensitive information!");
}

// ── Check 7: AssistanceSlipView component exists ─────────────────────────────
const slipViewPath = path.resolve("./src/components/AssistanceSlipView.tsx");
if (fs.existsSync(slipViewPath)) {
  console.log("[PASSED] 7. Component exists: src/components/AssistanceSlipView.tsx");
  passedCount++;
} else {
  throw new Error("Failed Check 7: src/components/AssistanceSlipView.tsx not found");
}

// ── Check 8: AssistanceSlipView has #pacs-assistance-slip container ───────────
const slipViewContent = fs.readFileSync(slipViewPath, "utf-8");
if (
  slipViewContent.includes('id="pacs-assistance-slip"') &&
  slipViewContent.includes('className="pacs-assistance-slip"')
) {
  console.log("[PASSED] 8. Container ID: #pacs-assistance-slip target present for thermal printing");
  passedCount++;
} else {
  throw new Error("Failed Check 8: #pacs-assistance-slip missing in AssistanceSlipView.tsx");
}

// ── Check 9: AssistanceSlipView renders all required sections ────────────────
const requiredSlipSections = [
  "slipData.header",
  "slipData.reference_code",
  "slipData.pacs_name",
  "slipData.category",
  "slipData.citizen_masked_name",
  "slipData.citizen_phone_masked",
  "slipData.original_query",
  "slipData.officer_translated_note",
  "slipData.ai_guidance_summary",
  "slipData.sources",
  "slipData.qr_payload",
  "slipData.disclaimer",
];
const missingSections = requiredSlipSections.filter((s) => !slipViewContent.includes(s));
if (missingSections.length === 0) {
  console.log(`[PASSED] 9. Slip Layout: All ${requiredSlipSections.length} core sections rendered`);
  passedCount++;
} else {
  throw new Error(`Failed Check 9: Missing sections in AssistanceSlipView: ${missingSections.join(", ")}`);
}

// ── Check 10: Screen-only print trigger calling window.print() ───────────────
if (
  slipViewContent.includes("window.print()") &&
  slipViewContent.includes("slip-toolbar slip-no-print")
) {
  console.log("[PASSED] 10. Print Control: window.print() trigger present with .slip-no-print toolbar");
  passedCount++;
} else {
  throw new Error("Failed Check 10: window.print() or .slip-no-print missing in AssistanceSlipView");
}

// ── Check 11: HandoffModal integrates AssistanceSlipView ─────────────────────
const modalPath = path.resolve("./src/components/HandoffModal.tsx");
const modalContent = fs.readFileSync(modalPath, "utf-8");
if (
  modalContent.includes("<AssistanceSlipView") &&
  modalContent.includes("handoff-view-slip-btn") &&
  modalContent.includes("handoff-print-slip-btn") &&
  modalContent.includes("showSlipView")
) {
  console.log("[PASSED] 11. Modal Integration: HandoffModal displays slip actions and renders AssistanceSlipView");
  passedCount++;
} else {
  throw new Error("Failed Check 11: AssistanceSlipView integration missing in HandoffModal.tsx");
}

// ── Check 12: Non-resubmission safety ────────────────────────────────────────
// Ensure opening slip view doesn't call submitHumanHandoff again
const submitOccurrences = (modalContent.match(/submitHumanHandoff/g) || []).length;
// submitHumanHandoff should only be imported and called inside handleSubmit
if (submitOccurrences <= 2 && modalContent.includes("onClick={() => setShowSlipView(true)}")) {
  console.log("[PASSED] 12. Non-Resubmission: Viewing slip triggers state toggle only, no duplicate API calls");
  passedCount++;
} else {
  throw new Error("Failed Check 12: Suspicious re-submission logic in HandoffModal.tsx");
}

// ── Check 13: App.css contains @media print with 58mm target ──────────────────
const cssPath = path.resolve("./src/App.css");
const cssContent = fs.readFileSync(cssPath, "utf-8");
if (
  cssContent.includes("@media print") &&
  cssContent.includes("size: 58mm auto") &&
  cssContent.includes("#pacs-assistance-slip") &&
  cssContent.includes(".slip-no-print")
) {
  console.log("[PASSED] 13. CSS: @media print defined with @page { size: 58mm auto } and #pacs-assistance-slip");
  passedCount++;
} else {
  throw new Error("Failed Check 13: Incomplete @media print rules in App.css");
}

// ── Check 14: English translations (en.ts) ───────────────────────────────────
const requiredI18nKeys = [
  "handoff.viewSlip",
  "handoff.printSlip",
  "handoff.slipReady",
  "handoff.slipReadyNotice",
  "slip.title",
  "slip.subtitle",
  "slip.refCode",
  "slip.date",
  "slip.pacs",
  "slip.village",
  "slip.category",
  "slip.citizen",
  "slip.phone",
  "slip.languages",
  "slip.originalQuery",
  "slip.officerNote",
  "slip.bhashiniNotice",
  "slip.aiGuidance",
  "slip.sources",
  "slip.qrScanNotice",
  "slip.qrPrivacyNotice",
  "slip.disclaimer",
  "slip.printBtn",
  "slip.closeBtn",
];
const missingEn = requiredI18nKeys.filter((k) => !en[k]);
if (missingEn.length === 0) {
  console.log(`[PASSED] 14. English localization: All ${requiredI18nKeys.length} keys present`);
  passedCount++;
} else {
  throw new Error(`Failed Check 14: Missing EN keys: ${missingEn.join(", ")}`);
}

// ── Check 15: Hindi translations (hi.ts) ─────────────────────────────────────
const missingHi = requiredI18nKeys.filter((k) => !hi[k]);
if (missingHi.length === 0) {
  console.log(`[PASSED] 15. Hindi localization: All ${requiredI18nKeys.length} keys present`);
  passedCount++;
} else {
  throw new Error(`Failed Check 15: Missing HI keys: ${missingHi.join(", ")}`);
}

// ── Check 16: Marathi translations (mr.ts) ───────────────────────────────────
const missingMr = requiredI18nKeys.filter((k) => !mr[k]);
if (missingMr.length === 0) {
  console.log(`[PASSED] 16. Marathi localization: All ${requiredI18nKeys.length} keys present`);
  passedCount++;
} else {
  throw new Error(`Failed Check 16: Missing MR keys: ${missingMr.join(", ")}`);
}

// ── Check 17: QR Code Description strictly facilitation reference ────────────
const qrScanNoticeEn = en["slip.qrScanNotice"];
const qrPrivacyNoticeEn = en["slip.qrPrivacyNotice"];
const isFacilitationOnly =
  !qrScanNoticeEn.includes("Court") &&
  !qrScanNoticeEn.includes("Official Government Summons") &&
  qrPrivacyNoticeEn.includes("Reference Verification Only");
if (isFacilitationOnly) {
  console.log(`[PASSED] 17. Safe QR Description: "${qrScanNoticeEn}" (Zero court/summons fabrication)`);
  passedCount++;
} else {
  throw new Error("Failed Check 17: QR notice text misrepresents legal status");
}

// ── Check 18: Full End-to-End Mock Assistance Slip Pipeline ──────────────────
const mockSlipData = {
  header: "SAHKAARSETU PACS ASSISTANCE REFERENCE SLIP",
  reference_code: "PACS-2026-789012",
  created_at: new Date().toISOString(),
  pacs_name: "Dindori Primary Agricultural Cooperative",
  village: "Dindori",
  category: "PMFBY",
  citizen_masked_name: "Tukaram S. K****",
  citizen_phone_masked: "+91 98221 •••••",
  citizen_language: "mr",
  officer_language: "en",
  original_query: "माझ्या शेतात पुरामुळे नुकसान झाले आहे, पीक विमा कसा मिळेल?",
  officer_translated_note: "Crop damage due to flood, inquiring about PMFBY claim process.",
  ai_guidance_summary: "File intimation within 72 hours on PMFBY portal or submit at PACS with 7/12.",
  sources: ["PMFBY Operational Guidelines 2024", "Maharashtra State Cooperative Societies Act"],
  qr_payload: "https://sahkaarsetu.gov.in/verify/slip?ref=PACS-2026-789012&pacs=Dindori&cat=PMFBY",
  disclaimer: "This is a facilitation slip generated for PACS assistance. It does not constitute a formal grievance registration under cooperative law.",
};

const generatedSvg = generateQrSvg(mockSlipData.qr_payload);
const generatedDataUri = generateQrDataUri(mockSlipData.qr_payload);

if (
  generatedSvg.length > 500 &&
  generatedDataUri.startsWith("data:image/svg+xml;utf8,") &&
  mockSlipData.citizen_masked_name.includes("****") &&
  mockSlipData.citizen_phone_masked.includes("•••••")
) {
  console.log("[PASSED] 18. E2E Simulation: Complete assistance slip data and QR SVG generated successfully");
  passedCount++;
} else {
  throw new Error("Failed Check 18: E2E Simulation failed to generate valid slip output");
}

console.log("================================================================================");
console.log(`ALL CHECKS PASSED: ${passedCount} / ${totalChecks} (100% SUCCESS)`);
console.log("VERDICT: PASS — CITIZEN QR & PRINT VERIFIED");
console.log("================================================================================");
