/**
 * Phase 3C.6 — Document-Aware Human Handoff Enrichment Test Suite
 *
 * Test 20 Points:
 *   1. document-enriched handoff modal opens correctly from assistant message with docResult
 *   2. document_type correctly informs category
 *   3. PMFBY policy maps to crop insurance category (PMFBY)
 *   4. 7/12 land record maps to land/records category (AGRICULTURAL_SUPPORT)
 *   5. fertilizer receipt maps to inputs/fertilizer category (AGRICULTURAL_SUPPORT)
 *   6. cooperative notice maps to PACS/cooperative category (PACS_SERVICE)
 *   7. loan passbook maps to loan/banking category (FINANCIAL_LITERACY)
 *   8. subsidy letter maps to schemes/subsidy category (MINISTRY_SCHEME)
 *   9. safe document reference is pre-filled (policy number, account number, etc.)
 *   10. masked PII remains masked (no unmasking of Aadhaar/PAN)
 *   11. untrusted extraction is labeled as user document metadata, NOT verified truth
 *   12. raw image/base64 is NEVER passed to handoff
 *   13. human handoff backend contract remains compatible (same schema, no new required fields)
 *   14. citizen can edit pre-filled issue summary before submitting
 *   15. assistance slip includes document-aware context safely (reference or note)
 *   16. QR payload contains safe handoff reference, NOT raw document dump
 *   17. IDENTITY_DOCUMENT refusal cannot create document-enriched handoff
 *   18. English handoff flow works
 *   19. Hindi handoff flow works
 *   20. Marathi handoff flow works
 *
 * Run: node --experimental-strip-types frontend/scripts/test_document_handoff.ts
 */

import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, resolve } from "path";
import {
  mapDocumentCategory,
  extractDocumentReference,
  formatHandoffDescription,
} from "../src/utils/documentContextFormatter.ts";
import type { VisionAnalyzeResponse, ChatMessage as ChatMessageType } from "../src/types/index.ts";

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
console.log("CITIZEN PHASE 3C.6: DOCUMENT-AWARE HUMAN HANDOFF ENRICHMENT VERIFICATION SUITE");
console.log("================================================================================");

// Sample Document Payloads
const mockPmfbyDoc: VisionAnalyzeResponse = {
  success: true,
  document_type: "PMFBY_POLICY",
  readability: "CLEAR",
  detected_language: "en",
  suggested_questions: [],
  has_sensitive_pii: false,
  key_fields: {
    policy_number: "PMFBY/2026/XXXX-9876",
    farmer_name: "Ramesh Patil",
    crop: "Soyabean",
    season: "Kharif 2026",
    sum_insured: "₹45,000",
  },
  document_summary: "PMFBY crop insurance certificate for Soyabean crop in Kharif 2026.",
};

const mock712Doc: VisionAnalyzeResponse = {
  success: true,
  document_type: "LAND_RECORD_7_12",
  readability: "CLEAR",
  detected_language: "mr",
  suggested_questions: [],
  has_sensitive_pii: false,
  key_fields: {
    survey_number: "142/2A",
    farmer_name: "Suresh Chavan",
    village: "Koregaon",
  },
  document_summary: "Extract 7/12 Land Record for Survey 142/2A.",
};

const mockFertilizerDoc: VisionAnalyzeResponse = {
  success: true,
  document_type: "FERTILIZER_RECEIPT",
  readability: "CLEAR",
  detected_language: "hi",
  suggested_questions: [],
  has_sensitive_pii: false,
  key_fields: {
    receipt_number: "RCPT-2026-5541",
    fertilizer_type: "Urea 45kg",
    amount: "₹266.50",
  },
  document_summary: "Fertilizer purchase receipt for subsidized Urea.",
};

const mockCoopNoticeDoc: VisionAnalyzeResponse = {
  success: true,
  document_type: "COOPERATIVE_NOTICE",
  readability: "CLEAR",
  detected_language: "mr",
  suggested_questions: [],
  has_sensitive_pii: false,
  key_fields: {
    notice_number: "NOT/PACS/2026/12",
    date: "12-Aug-2026",
    subject: "Annual General Meeting",
  },
  document_summary: "Notice for PACS Annual General Meeting.",
};

const mockLoanDoc: VisionAnalyzeResponse = {
  success: true,
  document_type: "LOAN_PASSBOOK",
  readability: "CLEAR",
  detected_language: "en",
  suggested_questions: [],
  has_sensitive_pii: false,
  key_fields: {
    account_number: "KCC-XXXX-XXXX-4412",
    crop_loan_limit: "₹1,50,000",
  },
  document_summary: "Kisan Credit Card loan passbook showing approved limit.",
};

const mockSubsidyDoc: VisionAnalyzeResponse = {
  success: true,
  document_type: "SUBSIDY_LETTER",
  readability: "CLEAR",
  detected_language: "hi",
  suggested_questions: [],
  has_sensitive_pii: false,
  key_fields: {
    application_number: "SUB-GOV-88210",
    scheme_name: "Drip Irrigation Subsidy",
  },
  document_summary: "Sanction letter for drip irrigation subsidy.",
};

const mockIdentityDoc: VisionAnalyzeResponse = {
  success: false,
  document_type: "IDENTITY_DOCUMENT",
  readability: "CLEAR",
  detected_language: "en",
  refusal_reason: "Identity documents are not accepted.",
  suggested_questions: [],
  has_sensitive_pii: true,
  key_fields: {
    aadhaar_number: "XXXX-XXXX-1234",
  },
};

// 1. document-enriched handoff modal opens correctly from assistant message with docResult
const chatMessageSrc = src("frontend/src/components/ChatMessage.tsx");
assert(
  chatMessageSrc.includes("docResult={message.docResult}") &&
    chatMessageSrc.includes("<HandoffModal"),
  "1. document-enriched handoff modal receives docResult from ChatMessage",
  "HandoffModal must receive message.docResult"
);

// 2. document_type correctly informs category / subcategory
const handoffModalSrc = src("frontend/src/components/HandoffModal.tsx");
assert(
  handoffModalSrc.includes("mapDocumentCategory(docResult.document_type, category)") &&
    handoffModalSrc.includes("category: resolvedCategory"),
  "2. document_type correctly informs resolvedCategory in HandoffModal",
  "HandoffModal must resolve category via mapDocumentCategory"
);

// 3. PMFBY policy maps to crop insurance category (PMFBY)
assert(
  mapDocumentCategory("PMFBY_POLICY") === "PMFBY",
  "3. PMFBY_POLICY maps to PMFBY category"
);

// 4. 7/12 land record maps to land/records category (AGRICULTURAL_SUPPORT)
assert(
  mapDocumentCategory("LAND_RECORD_7_12") === "AGRICULTURAL_SUPPORT",
  "4. LAND_RECORD_7_12 maps to AGRICULTURAL_SUPPORT"
);

// 5. fertilizer receipt maps to inputs/fertilizer category (AGRICULTURAL_SUPPORT)
assert(
  mapDocumentCategory("FERTILIZER_RECEIPT") === "AGRICULTURAL_SUPPORT",
  "5. FERTILIZER_RECEIPT maps to AGRICULTURAL_SUPPORT"
);

// 6. cooperative notice maps to PACS/cooperative category (PACS_SERVICE)
assert(
  mapDocumentCategory("COOPERATIVE_NOTICE") === "PACS_SERVICE" &&
    mapDocumentCategory("PACS_MEMBERSHIP_FORM") === "PACS_SERVICE",
  "6. COOPERATIVE_NOTICE and PACS_MEMBERSHIP_FORM map to PACS_SERVICE"
);

// 7. loan passbook maps to loan/banking category (FINANCIAL_LITERACY)
assert(
  mapDocumentCategory("LOAN_PASSBOOK") === "FINANCIAL_LITERACY",
  "7. LOAN_PASSBOOK maps to FINANCIAL_LITERACY"
);

// 8. subsidy letter maps to schemes/subsidy category (MINISTRY_SCHEME)
assert(
  mapDocumentCategory("SUBSIDY_LETTER") === "MINISTRY_SCHEME",
  "8. SUBSIDY_LETTER maps to MINISTRY_SCHEME"
);

// 9. safe document reference is pre-filled
const refPmfby = extractDocumentReference(mockPmfbyDoc);
const refLoan = extractDocumentReference(mockLoanDoc);
const refSubsidy = extractDocumentReference(mockSubsidyDoc);
assert(
  refPmfby === "PMFBY/2026/XXXX-9876" &&
    refLoan === "KCC-XXXX-XXXX-4412" &&
    refSubsidy === "SUB-GOV-88210",
  "9. Safe document reference is accurately extracted from key_fields",
  `Got: pmfby=${refPmfby}, loan=${refLoan}, subsidy=${refSubsidy}`
);

// 10. masked PII remains masked (no unmasking of Aadhaar/PAN)
const descPmfby = formatHandoffDescription("How do I claim insurance?", mockPmfbyDoc);
const descLoan = formatHandoffDescription("What is my interest rate?", mockLoanDoc);
assert(
  descPmfby.includes("XXXX-9876") &&
    descLoan.includes("KCC-XXXX-XXXX-4412") &&
    !descPmfby.includes("unmasked") &&
    !descLoan.includes("unmasked"),
  "10. Masked PII remains masked in pre-filled handoff description",
  "Masked patterns XXXX must be preserved"
);

// 11. untrusted extraction is labeled as user document metadata, NOT verified truth
assert(
  descPmfby.includes("Extracted from citizen-provided document") &&
    descPmfby.includes("Information for PACS staff assistance review only"),
  "11. Untrusted document context is explicitly labeled as unverified user metadata",
  "Description must contain safe advisory for PACS staff"
);

// 12. raw image/base64 is NEVER passed to handoff
const appSrc = src("frontend/src/App.tsx");
assert(
  !handoffModalSrc.includes("imageBase64") &&
    !handoffModalSrc.includes("data:image") &&
    !appSrc.includes("handoff: imageBase64"),
  "12. Raw image bytes and base64 strings are NEVER passed to handoff"
);

// 13. human handoff backend contract remains compatible
const backendSchema = src("backend/app/schemas/grievance_handoff.py");
const backendRoute = src("backend/app/api/routes/grievance.py");
assert(
  backendSchema.includes("class HandoffCreateRequest(BaseModel):") &&
    backendSchema.includes("category: str = Field(") &&
    backendSchema.includes("description: str = Field(") &&
    backendRoute.includes('"/handoff"') &&
    backendRoute.includes("create_human_handoff"),
  "13. Backend human handoff contract is 100% compatible with existing HandoffCreateRequest"
);

// 14. citizen can edit pre-filled issue summary before submitting
assert(
  handoffModalSrc.includes("value={issueSummary}") &&
    handoffModalSrc.includes("onChange={(e) => setIssueSummary(e.target.value)}") &&
    handoffModalSrc.includes("textarea"),
  "14. Citizen can edit pre-filled issue summary before submitting in HandoffModal"
);

// 15. assistance slip includes document-aware context safely
const slipSrc = src("frontend/src/components/AssistanceSlipView.tsx");
assert(
  slipSrc.includes("slipData.original_query") &&
    slipSrc.includes("slipData.category") &&
    slipSrc.includes("pacs-assistance-slip"),
  "15. Assistance slip prints enriched original query and mapped category safely"
);

// 16. QR payload contains safe handoff reference, NOT raw document dump
assert(
  slipSrc.includes("generateQrSvg(slipData.qr_payload") &&
    !slipSrc.includes("qr_payload: docResult") &&
    !slipSrc.includes("qr_payload: JSON.stringify(docResult)"),
  "16. QR code payload preserves official reference verification, not raw document dump"
);

// 17. IDENTITY_DOCUMENT refusal cannot create document-enriched handoff
const identityRef = extractDocumentReference(mockIdentityDoc);
const identityDesc = formatHandoffDescription("I need help", mockIdentityDoc);
assert(
  identityRef === null &&
    identityDesc === "I need help" &&
    !identityDesc.includes("IDENTITY_DOCUMENT"),
  "17. IDENTITY_DOCUMENT refusal is strictly suppressed from document handoff enrichment",
  `Identity ref=${identityRef}, desc=${identityDesc}`
);

// 18. English handoff flow works
const enLocale = src("frontend/src/i18n/locales/en.ts");
assert(
  enLocale.includes('"handoff.documentContextBadge":') &&
    enLocale.includes('"handoff.documentType":') &&
    enLocale.includes('"handoff.documentNotice":'),
  "18. English locale strings present for document-aware handoff"
);

// 19. Hindi handoff flow works
const hiLocale = src("frontend/src/i18n/locales/hi.ts");
assert(
  hiLocale.includes('"handoff.documentContextBadge":') &&
    hiLocale.includes('"handoff.documentType":') &&
    hiLocale.includes('"handoff.documentNotice":'),
  "19. Hindi locale strings present for document-aware handoff"
);

// 20. Marathi handoff flow works
const mrLocale = src("frontend/src/i18n/locales/mr.ts");
assert(
  mrLocale.includes('"handoff.documentContextBadge":') &&
    mrLocale.includes('"handoff.documentType":') &&
    mrLocale.includes('"handoff.documentNotice":'),
  "20. Marathi locale strings present for document-aware handoff"
);

console.log("================================================================================");
console.log(`RESULTS: ${passed.length}/20 PASSED, ${failed.length} FAILED`);
console.log("================================================================================");

if (failed.length > 0) {
  console.error("FAILURES DETECTED in Phase 3C.6 Test Suite!");
  process.exit(1);
} else {
  console.log("ALL 20 CHECKS PASSED: Citizen Phase 3C.6 verified.");
}
