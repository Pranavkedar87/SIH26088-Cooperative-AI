# Citizen Phase 3C.6 — Document-Aware Human Handoff Enrichment Implementation Report

**Project:** SAHKAARSETU / SIH26088  
**Phase:** Citizen Phase 3C.6 — Document-Aware Human Handoff Enrichment  
**Date:** September 15, 2026  
**Status:** COMPLETED & VERIFIED  

---

## 1. Executive Summary

When a citizen scans a physical document (such as a PMFBY crop insurance certificate, 7/12 land record, fertilizer purchase receipt, or KCC loan passbook), receives a grounded AI response, and decides to request in-person or administrative assistance via **"Get Help from PACS"**, Phase 3C.6 enriches the human handoff flow with the already-analyzed document context.

This enrichment is achieved **without modifying any backend endpoints**, **without database migrations**, and **without violating source purity or privacy constraints**:
- **Source Purity:** The scanned document is strictly treated as untrusted, user-provided reference data. It is **never** added to official source citations (`source_citations` or `sources`).
- **PII Protection:** Only already-redacted, masked strings (`XXXX-XXXX-NNNN`) are propagated. Raw image bytes and base64 strings are **never** passed to the handoff pipeline.
- **Identity Document Refusal Guard:** Documents categorized as `IDENTITY_DOCUMENT` (Aadhaar, PAN, Voter ID) are refused, preventing their details from enriching handoff summaries.
- **Backend Contract Preservation:** Utilizes the existing `POST /api/grievance/handoff` endpoint and `HandoffCreateRequest` schema without modification. Category mappings translate vision document types directly to recognized backend categories.

---

## 2. Architecture & Data Flow

```
┌───────────────────────────┐
│ 📷 Scanned Document Image │
└─────────────┬─────────────┘
              │ (POST /api/vision/analyze)
              ▼
┌───────────────────────────┐
│   VisionAnalyzeResponse   │
└─────────────┬─────────────┘
              │ (DocumentAnalysisModal)
              ▼
┌───────────────────────────┐
│    Governed RAG Query     │ ◄── <untrusted_document_context>
└─────────────┬─────────────┘
              │ (Grounded Answer + Official Citations)
              ▼
┌───────────────────────────┐
│   Assistant ChatMessage   │ ── docResult attached to turn
└─────────────┬─────────────┘
              │ "Get Help from PACS" CTA
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      HandoffModal (Enriched)                    │
│                                                                 │
│  • Category Mapping: PMFBY_POLICY -> PMFBY                      │
│                      LAND_RECORD_7_12 -> AGRICULTURAL_SUPPORT   │
│                      FERTILIZER_RECEIPT -> AGRICULTURAL_SUPPORT │
│                      COOPERATIVE_NOTICE -> PACS_SERVICE         │
│                      LOAN_PASSBOOK -> FINANCIAL_LITERACY        │
│                      SUBSIDY_LETTER -> MINISTRY_SCHEME          │
│                                                                 │
│  • Pre-filled Issue Summary: Editable by citizen                │
│    - Citizen question                                           │
│    - Safe attached document type                                │
│    - Safe redacted reference (e.g. PMFBY/2026/XXXX-9876)        │
│    - PACS review notice (unverified user-provided doc)          │
│                                                                 │
│  • Visual Badge: Scanned Document Context attached              │
└─────────────────────────────┬───────────────────────────────────┘
                              │ POST /api/grievance/handoff (UNTOUCHED)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Assistance Slip & Thermal Print                 │
│                                                                 │
│  • Reference Code (e.g. PACS-2026-LESK9F)                       │
│  • Mapped Category                                              │
│  • Enriched Original Query & Document Reference                 │
│  • Offline QR Code (Verification payload only, NO raw document) │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Files Modified & Additions

### Frontend
1. **`frontend/src/types/index.ts`**
   - Added optional `docResult?: VisionAnalyzeResponse` to the `ChatMessage` interface.
2. **`frontend/src/App.tsx`**
   - Attached `docResult: docResult || undefined` to the assistant `ChatMessage` turn when saving and displaying RAG responses.
3. **`frontend/src/components/ChatMessage.tsx`**
   - Forwarded `docResult={message.docResult}` from message state to `<HandoffModal />`.
4. **`frontend/src/utils/documentContextFormatter.ts`**
   - Added `mapDocumentCategory(docType, fallbackCategory)`: Deterministically maps vision document types to existing backend grievance categories.
   - Added `extractDocumentReference(docResult)`: Safely extracts already-redacted reference identifiers (`policy_number`, `account_number`, `receipt_number`, etc.), returning `null` on `IDENTITY_DOCUMENT`.
   - Added `formatHandoffDescription(citizenQuestion, docResult)`: Formats pre-filled handoff description clearly distinguishing the citizen question, attached document type/reference, and an advisory notice that the document is unverified user metadata for staff assistance review.
5. **`frontend/src/components/HandoffModal.tsx`**
   - Added `docResult?: VisionAnalyzeResponse | null` to props.
   - Initialized `resolvedCategory` using `mapDocumentCategory`.
   - Prefilled editable `issueSummary` using `formatHandoffDescription`.
   - Rendered a clean, accessible badge in the context card displaying the attached document type and safe reference.
6. **`frontend/src/i18n/locales/en.ts`, `hi.ts`, `mr.ts`**
   - Added localized strings for `handoff.documentContextBadge`, `handoff.documentType`, `handoff.documentRef`, `handoff.documentNotice`, `slip.documentType`, and `slip.documentRef`.

### Test Suite
- **`frontend/scripts/test_document_handoff.ts`**: Comprehensive automated verification suite testing all 20 required points.

---

## 4. Verification & Test Results

### 1. Phase 3C.6 Document Handoff Test Suite (`test_document_handoff.ts`)
Run: `node --experimental-strip-types frontend/scripts/test_document_handoff.ts`
```
================================================================================
CITIZEN PHASE 3C.6: DOCUMENT-AWARE HUMAN HANDOFF ENRICHMENT VERIFICATION SUITE
================================================================================
  ✓ 1. document-enriched handoff modal receives docResult from ChatMessage
  ✓ 2. document_type correctly informs resolvedCategory in HandoffModal
  ✓ 3. PMFBY_POLICY maps to PMFBY category
  ✓ 4. LAND_RECORD_7_12 maps to AGRICULTURAL_SUPPORT
  ✓ 5. FERTILIZER_RECEIPT maps to AGRICULTURAL_SUPPORT
  ✓ 6. COOPERATIVE_NOTICE and PACS_MEMBERSHIP_FORM map to PACS_SERVICE
  ✓ 7. LOAN_PASSBOOK maps to FINANCIAL_LITERACY
  ✓ 8. SUBSIDY_LETTER maps to MINISTRY_SCHEME
  ✓ 9. Safe document reference is accurately extracted from key_fields
  ✓ 10. Masked PII remains masked in pre-filled handoff description
  ✓ 11. Untrusted document context is explicitly labeled as unverified user metadata
  ✓ 12. Raw image bytes and base64 strings are NEVER passed to handoff
  ✓ 13. Backend human handoff contract is 100% compatible with existing HandoffCreateRequest
  ✓ 14. Citizen can edit pre-filled issue summary before submitting in HandoffModal
  ✓ 15. Assistance slip prints enriched original query and mapped category safely
  ✓ 16. QR code payload preserves official reference verification, not raw document dump
  ✓ 17. IDENTITY_DOCUMENT refusal is strictly suppressed from document handoff enrichment
  ✓ 18. English locale strings present for document-aware handoff
  ✓ 19. Hindi locale strings present for document-aware handoff
  ✓ 20. Marathi locale strings present for document-aware handoff
================================================================================
RESULTS: 20/20 PASSED, 0 FAILED
================================================================================
ALL 20 CHECKS PASSED: Citizen Phase 3C.6 verified.
```

### 2. Frontend Production Build
Run: `cd frontend && npm run build`
- Type checking (`tsc -b`): Passed cleanly.
- Vite build: Completed successfully (`dist/assets/index-DVAvEGvM.js`, 603.05 kB).

### 3. Regressions & Related Test Suites
- **Vision RAG Integration Suite (`test_vision_rag_integration.ts`)**: 47/47 Passed.
- **Vision UI Suite (`test_vision_ui.ts`)**: 80/80 Passed.
- **Human Handoff UI Suite (`test_handoff_ui.ts`)**: 13/13 Passed.
- **Assistance Slip & QR Suite (`test_handoff_slip.ts`)**: 18/18 Passed.
- **Backend Vision Suite (`test_vision_scan.py`)**: 20/20 Passed.
- **Backend Human Handoff Suite (`test_human_handoff_backend.py`)**: 17/17 Passed.
- **Backend Citizen & Core Regression Suite (`test_citizen_regression.py`)**: 6/6 Passed.

---

## 5. Security & Boundary Conformance

| Boundary | Compliance | Detail |
| :--- | :---: | :--- |
| **Backend Frozen** | YES | Zero backend routes, schemas, or database tables modified. |
| **Admin Frozen** | YES | Sarkar Setu Admin repository completely untouched. |
| **Source Purity** | YES | Scanned document never injected into `source_citations` or `sources`. |
| **PII Protection** | YES | No unmasking or raw numbers passed; preserves `XXXX-XXXX-NNNN` masking. |
| **Refusal Enforcement** | YES | Identity documents cannot trigger document-enriched handoffs. |
| **Raw Media Isolation** | YES | Raw images/base64 strings never touch handoff or slip payloads. |

---

## 6. Final Verdict

**PASS — DOCUMENT HANDOFF ENRICHMENT VERIFIED**
