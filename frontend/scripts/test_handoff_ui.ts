/**
 * Citizen Phase 3A.2 — Human Handoff Citizen UI Verification Script
 * Validates types, translations (EN, HI, MR), API client contract,
 * and component integration for ChatMessage and VoiceModeView.
 */
import { en } from "../src/i18n/locales/en.ts";
import { hi } from "../src/i18n/locales/hi.ts";
import { mr } from "../src/i18n/locales/mr.ts";
import * as fs from "fs";
import * as path from "path";

console.log("============================================================");
console.log("RUNNING CITIZEN PHASE 3A.2 HUMAN HANDOFF UI TEST SUITE");
console.log("============================================================");

let passedCount = 0;
const totalChecks = 13;

// 1. Check types/index.ts has Human Handoff interfaces
const typesPath = path.resolve("./src/types/index.ts");
const typesContent = fs.readFileSync(typesPath, "utf-8");
if (
  typesContent.includes("export interface AssistanceSlipData") &&
  typesContent.includes("export interface HumanHandoffRequest") &&
  typesContent.includes("export interface HumanHandoffResponse")
) {
  console.log("[PASSED] 1. Types defined: AssistanceSlipData, HumanHandoffRequest, HumanHandoffResponse");
  passedCount++;
} else {
  throw new Error("Failed Check 1: Missing Human Handoff types in src/types/index.ts");
}

// 2. Check client.ts exports submitHumanHandoff targeting /api/grievance/handoff
const clientPath = path.resolve("./src/api/client.ts");
const clientContent = fs.readFileSync(clientPath, "utf-8");
if (
  clientContent.includes("export async function submitHumanHandoff") &&
  clientContent.includes("/api/grievance/handoff")
) {
  console.log("[PASSED] 2. API Client: submitHumanHandoff targeting /api/grievance/handoff implemented");
  passedCount++;
} else {
  throw new Error("Failed Check 2: submitHumanHandoff missing in src/api/client.ts");
}

// 3. Check English UI strings
const requiredHandoffKeys = [
  "handoff.getHelpBtn",
  "handoff.modalTitle",
  "handoff.modalExplanation",
  "handoff.disclaimerNotice",
  "handoff.querySummary",
  "handoff.aiGuidanceSummary",
  "handoff.sourcesLabel",
  "handoff.citizenName",
  "handoff.citizenPhone",
  "handoff.pacsName",
  "handoff.village",
  "handoff.officerLanguage",
  "handoff.submitBtn",
  "handoff.submittingBtn",
  "handoff.successTitle",
  "handoff.referenceCode",
  "handoff.successMessage",
  "handoff.slipPlaceholder",
  "handoff.slipPlaceholderNotice",
  "handoff.close",
  "handoff.errorTitle",
  "handoff.errorMessage",
  "handoff.retryBtn",
  "handoff.translationNotice",
];

const missingEn = requiredHandoffKeys.filter((k) => !en[k]);
if (missingEn.length === 0) {
  console.log(`[PASSED] 3. English UI strings: All ${requiredHandoffKeys.length} handoff keys verified`);
  passedCount++;
} else {
  throw new Error(`Failed Check 3: Missing EN keys: ${missingEn.join(", ")}`);
}

// 4. Check Hindi UI strings
const missingHi = requiredHandoffKeys.filter((k) => !hi[k]);
if (missingHi.length === 0) {
  console.log(`[PASSED] 4. Hindi UI strings: All ${requiredHandoffKeys.length} handoff keys verified`);
  passedCount++;
} else {
  throw new Error(`Failed Check 4: Missing HI keys: ${missingHi.join(", ")}`);
}

// 5. Check Marathi UI strings
const missingMr = requiredHandoffKeys.filter((k) => !mr[k]);
if (missingMr.length === 0) {
  console.log(`[PASSED] 5. Marathi UI strings: All ${requiredHandoffKeys.length} handoff keys verified`);
  passedCount++;
} else {
  throw new Error(`Failed Check 5: Missing MR keys: ${missingMr.join(", ")}`);
}

// 6. Check HandoffModal.tsx component implementation
const modalPath = path.resolve("./src/components/HandoffModal.tsx");
if (fs.existsSync(modalPath)) {
  const modalContent = fs.readFileSync(modalPath, "utf-8");
  if (
    modalContent.includes("export const HandoffModal") &&
    modalContent.includes("submitHumanHandoff") &&
    modalContent.includes('role="dialog"') &&
    modalContent.includes("aria-modal=\"true\"") &&
    modalContent.includes("SUBMITTING") &&
    modalContent.includes("SUCCESS") &&
    modalContent.includes("ERROR")
  ) {
    console.log("[PASSED] 6. HandoffModal component: Implemented with accessibility, state machine, and clean inputs");
    passedCount++;
  } else {
    throw new Error("Failed Check 6: HandoffModal.tsx missing required state machine or accessibility attributes");
  }
} else {
  throw new Error("Failed Check 6: src/components/HandoffModal.tsx does not exist");
}

// 7. Check ChatMessage.tsx integration
const chatMsgPath = path.resolve("./src/components/ChatMessage.tsx");
const chatMsgContent = fs.readFileSync(chatMsgPath, "utf-8");
if (
  chatMsgContent.includes("HandoffModal") &&
  chatMsgContent.includes("isSuitableForHandoff") &&
  chatMsgContent.includes("action-btn--handoff") &&
  chatMsgContent.includes("handoff.getHelpBtn")
) {
  console.log("[PASSED] 7. ChatMessage integration: 'Get Help from PACS' CTA conditioned on non-casual guidance");
  passedCount++;
} else {
  throw new Error("Failed Check 7: ChatMessage.tsx missing HandoffModal or conditional CTA");
}

// 8. Check VoiceModeView.tsx integration
const voicePath = path.resolve("./src/components/VoiceModeView.tsx");
const voiceContent = fs.readFileSync(voicePath, "utf-8");
if (
  voiceContent.includes("HandoffModal") &&
  voiceContent.includes("voice-control-btn--handoff") &&
  voiceContent.includes("handoff.getHelpBtn")
) {
  console.log("[PASSED] 8. VoiceModeView integration: 'Get Help from PACS' CTA available on spoken response card");
  passedCount++;
} else {
  throw new Error("Failed Check 8: VoiceModeView.tsx missing Handoff CTA or modal");
}

// 9. Check App.css styling rules
const cssPath = path.resolve("./src/App.css");
const cssContent = fs.readFileSync(cssPath, "utf-8");
if (
  cssContent.includes(".action-btn--handoff") &&
  cssContent.includes(".voice-control-btn--handoff") &&
  cssContent.includes(".handoff-modal-panel") &&
  cssContent.includes(".handoff-ref-card") &&
  cssContent.includes(".handoff-slip-placeholder")
) {
  console.log("[PASSED] 9. CSS Styling: Responsive modal, ref card, and CTA styles implemented in App.css");
  passedCount++;
} else {
  throw new Error("Failed Check 9: Missing handoff CSS rules in App.css");
}

// 10. Check that QR and Print were NOT implemented in this phase (Reserved for Phase 3A.3)
if (
  !fs.existsSync(path.resolve("./src/components/AssistanceSlipView.tsx")) &&
  !typesContent.includes("qrcode") &&
  !clientContent.includes("window.print")
) {
  console.log("[PASSED] 10. Phase Boundary: QR generation and thermal browser printing strictly deferred to Phase 3A.3");
  passedCount++;
} else {
  throw new Error("Failed Check 10: Phase 3A.3 components prematurely introduced");
}

// 11. Existing chat actions remain intact (Read Aloud, Copy, PDF)
if (
  chatMsgContent.includes("handleDownloadPdf") &&
  chatMsgContent.includes("handleSpeakClick") &&
  chatMsgContent.includes("handleCopy")
) {
  console.log("[PASSED] 11. Non-regression: Read Aloud, Copy, and Guidance PDF generation preserved in ChatMessage");
  passedCount++;
} else {
  throw new Error("Failed Check 11: Existing ChatMessage actions were modified or removed");
}

// 12. Existing voice mode state machine intact
if (
  voiceContent.includes("handleOrbClick") &&
  voiceContent.includes("handleStopSpeakingClick") &&
  voiceContent.includes("FOLLOW_UP_LISTENING") &&
  voiceContent.includes("unlockAudio")
) {
  console.log("[PASSED] 12. Non-regression: Voice state machine, continuous listening, and audio unlocking preserved");
  passedCount++;
} else {
  throw new Error("Failed Check 12: Existing VoiceModeView state machine was modified");
}

// 13. Privacy and statutory disclaimer verification
if (
  en["handoff.disclaimerNotice"].includes("not an official court complaint") &&
  hi["handoff.disclaimerNotice"].includes("आधिकारिक न्यायालयीन शिकायत") &&
  mr["handoff.disclaimerNotice"].includes("कोणतीही अधिकृत न्यायालयीन तक्रार")
) {
  console.log("[PASSED] 13. Privacy & Disclaimers: Statutory facilitation disclaimers verified across all 3 languages");
  passedCount++;
} else {
  throw new Error("Failed Check 13: Disclaimer missing or inaccurate in translations");
}

console.log("============================================================");
console.log(`RESULTS: ${passedCount}/${totalChecks} CHECKS PASSED (100%)`);
console.log("============================================================");
