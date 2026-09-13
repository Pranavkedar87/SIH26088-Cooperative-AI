# CITIZEN PHASE 3A — MULTILINGUAL HUMAN HANDOFF ARCHITECTURE AUDIT
**Project:** SahkaarSetu (SIH26088)  
**Date:** September 13, 2026  
**Audit Type:** Pre-Implementation Architecture, Codebase & Data Model Audit (Report-Only)  
**Target Repository:** `/Users/pranav/SIH26088-Cooperative-AI`  
**Admin Repository Checked:** `/Users/pranav/Sarkar Setu Admin` (Verified 100% Untouched)  

---

## 1. Executive Summary

This audit evaluates the feasibility, data contracts, and architectural path for implementing **"Get Help from PACS" / Multilingual Human Handoff** (Phase 3A) in the SahkaarSetu Citizen Portal.

The target human handoff workflow bridges the gap between AI voice guidance and physical village-level assistance:
```
Citizen speaks 
  → Bhashini ASR (Primary) / Groq Whisper (Fallback)
  → Governed RAG + Gemini 2.5 Flash
  → Grounded Answer + Official Sources
  → Bhashini TTS Playback
  → Citizen selects "Get Help from PACS" (पॅक्सकडून मदत मिळवा / पैक्स से सहायता लें)
  → Collects minimal necessary details (Citizen Name/Phone, Village/PACS, Specific Issue)
  → Pre-fills with grounded AI answer & official sources from current session
  → Translates summary for Local Officer via MeitY Bhashini NMT (e.g. Marathi ↔ English / Hindi)
  → Generates reference ID, QR verification payload, and 58mm thermal-printer-friendly slip
  → Automatically surfaces in existing Admin Grievance & Kiosk triage workflow
```

### Audit Key Findings:
1. **Zero New Subsystems Needed**: The backend database already has an operational `grievances` table with `pacs_name`, `citizen_masked_name`, `citizen_phone_masked`, `ai_guidance`, `staff_notes`, and linked `conversation_id`.
2. **Admin Portal Already Integrated**: `/Users/pranav/Sarkar Setu Admin` already displays, filters, and inspects these exact grievance records with full conversation transcripts. A handoff ticket created by the citizen will appear in the Admin Portal **with zero Admin code changes**.
3. **Bhashini NMT is Ready & Live**: `BhashiniProvider.translate_text()` is already implemented and verified with live HTTP 200 OK responses across English, Hindi, and Marathi (average latency ~380ms).
4. **Thermal Print Format Supported via CSS**: Clean 58mm thermal slips can be rendered directly in the browser using standard `@media print` CSS rules without adding hardware drivers or heavy libraries.
5. **QR Code Generation Requires Zero React Peer Conflicts**: Standard React 19 compatibility mandates avoiding older React 18 QR wrappers; a lightweight, framework-agnostic generator (`qrcode` library or native SVG utility) is recommended.

**Final Verdict:** **READY — MINIMAL ADDITIVE IMPLEMENTATION**

---

## 2. Current Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CITIZEN FRONTEND (React 19)                        │
│                                                                             │
│   VoiceModeView / ChatMessage                                               │
│   [ Citizen Spoken Question ]                                               │
│              │                                                              │
│              ▼                                                              │
│   POST /api/voice/transcribe (Bhashini ASR / Groq Whisper Fallback)         │
│              │                                                              │
│              ▼                                                              │
│   POST /api/query (Governed RAG + Gemini 2.5 Flash + Supabase Knowledge)    │
│              │                                                              │
│              ▼                                                              │
│   [ Grounded Answer + Citations + Spoken Audio (Bhashini TTS) ]             │
│              │                                                              │
│              │ Citizen clicks: [ Get Help from PACS / मदत मिळवा ]           │
│              ▼                                                              │
│   NEW: HandoffModal / AssistanceSlipView                                    │
│   - Pre-fills: Query, Answer Summary, Official Sources, Session ID          │
│   - Input: Citizen Name (opt), Phone (opt), PACS Name (opt)                 │
│              │                                                              │
│              ▼                                                              │
│   POST /api/grievance/handoff (Additive Endpoint)                           │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND API & DATA LAYER                           │
│                                                                             │
│   backend/app/api/routes/grievance.py                                       │
│   - If citizen_lang != officer_lang:                                        │
│       Calls BhashiniProvider.translate_text()                               │
│   - Calls repository.create_grievance()                                     │
│   - Links conversation_id & session_id                                      │
│   - Saves to Supabase PostgreSQL table: `grievances`                        │
│   - Returns: reference_id, qr_payload, slip_data, translated_summary        │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ADMIN PORTAL (Zero Changes)                        │
│                                                                             │
│   /Users/pranav/Sarkar Setu Admin/src/pages/GrievancesPage.tsx              │
│   - Calls GET /api/admin/grievances                                         │
│   - Instantly lists new handoff with:                                       │
│     * ID (e.g. GRV-2026-XXXX or UUID)                                      │
│     * Category & PACS Name                                                  │
│     * Masked Citizen Details                                                │
│     * AI Guidance & Citations                                               │
│     * Full Live Conversation Transcript from session!                       │
│     * Operator can assign staff, add verification notes, update status      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Existing Reusable Components

The following components and modules are already built, tested, and can be directly reused without modifications:

| Component / File | Capability | Reusability in Phase 3A |
| :--- | :--- | :--- |
| [`backend/app/providers/bhashini_provider.py`](file:///Users/pranav/SIH26088-Cooperative-AI/backend/app/providers/bhashini_provider.py) | `translate_text(text, source_lang, target_lang)` | **100% Reusable**: Already implements NMT translation via Bhashini Dhruva pipeline. |
| [`backend/database/repository.py`](file:///Users/pranav/SIH26088-Cooperative-AI/backend/database/repository.py) | `create_grievance()`, `list_admin_grievances()`, `get_admin_grievance_by_id()` | **100% Reusable**: Already persists records to Supabase with in-memory dev fallbacks and links conversation transcripts. |
| [`backend/app/api/routes/admin_grievances.py`](file:///Users/pranav/SIH26088-Cooperative-AI/backend/app/api/routes/admin_grievances.py) | `GET /api/admin/grievances`, `GET /api/admin/grievances/{id}` | **100% Reusable**: No changes required for Admin visibility. |
| [`frontend/src/services/locationService.ts`](file:///Users/pranav/SIH26088-Cooperative-AI/frontend/src/services/locationService.ts) | Geolocation & OSM district/state reverse geocoding | **100% Reusable**: Can pre-fill citizen's district/state into the handoff slip. |
| [`frontend/src/utils/languageDetector.ts`](file:///Users/pranav/SIH26088-Cooperative-AI/frontend/src/utils/languageDetector.ts) | Script & language detector | **100% Reusable**: Identifies citizen input language (en, hi, mr). |
| [`frontend/src/components/Icons.tsx`](file:///Users/pranav/SIH26088-Cooperative-AI/frontend/src/components/Icons.tsx) | SVG icons (`Building`, `Printer`, `QR`, `ShieldCheck`, `CheckCircle`) | **100% Reusable**: Existing clean iconography. |

---

## 4. Exact File Map

### A. Files to be Extended (Additive Only)
1. **[`backend/app/api/routes/grievance.py`](file:///Users/pranav/SIH26088-Cooperative-AI/backend/app/api/routes/grievance.py)**:
   - *Current Behavior*: Exposes `POST /api/grievance` (basic description/category) and `GET /api/grievance/{id}`.
   - *Proposed Extension*: Add `POST /api/grievance/handoff` accepting `HandoffCreateRequest` (citizen details, PACS name, query, AI guidance, sources, language, target officer language) that performs NMT translation via Bhashini and returns a structured slip response.
   - *Nature*: **Additive** (Zero impact on existing `POST /api/grievance`).
2. **[`backend/database/repository.py`](file:///Users/pranav/SIH26088-Cooperative-AI/backend/database/repository.py)**:
   - *Current Behavior*: `create_grievance()` accepts `conversation_id`, `category`, `description`, `status`.
   - *Proposed Extension*: Add optional parameters `pacs_name`, `citizen_name`, `citizen_phone`, `ai_guidance`, `priority` to `create_grievance()`, persisting them in Supabase and fallback dictionary.
   - *Nature*: **Additive** (Defaults ensure 100% backwards compatibility with existing callers).
3. **[`frontend/src/api/client.ts`](file:///Users/pranav/SIH26088-Cooperative-AI/frontend/src/api/client.ts)**:
   - *Current Behavior*: Provides `sendQuery()`, `transcribeAudio()`, `synthesizeSpeech()`, `checkHealth()`.
   - *Proposed Extension*: Add `submitHumanHandoff(payload: HandoffPayload)` calling `POST /api/grievance/handoff`.
   - *Nature*: **Additive**.
4. **[`frontend/src/types/index.ts`](file:///Users/pranav/SIH26088-Cooperative-AI/frontend/src/types/index.ts)**:
   - *Current Behavior*: Contains `ChatMessage`, `QueryRequest`, `QueryResponse`, etc.
   - *Proposed Extension*: Add TypeScript interfaces for `HandoffPayload`, `HandoffResponse`, and `AssistanceSlipData`.
   - *Nature*: **Additive**.
5. **[`frontend/src/components/ChatMessage.tsx`](file:///Users/pranav/SIH26088-Cooperative-AI/frontend/src/components/ChatMessage.tsx)**:
   - *Current Behavior*: Shows "Download PDF", "Read Aloud", "Copy".
   - *Proposed Extension*: Add action button `"Get Help from PACS"` when message contains assistance guidance, opening the Handoff Modal.
   - *Nature*: **Additive**.
6. **[`frontend/src/components/VoiceModeView.tsx`](file:///Users/pranav/SIH26088-Cooperative-AI/frontend/src/components/VoiceModeView.tsx)**:
   - *Current Behavior*: Displays spoken response card with "Listen Again" and "View Text Chat".
   - *Proposed Extension*: Add `"Get Help from PACS"` button directly on the voice response card so voice users can generate a slip with one tap.
   - *Nature*: **Additive**.

### B. New Files to Create
1. **[`frontend/src/components/HandoffModal.tsx`](file:///Users/pranav/SIH26088-Cooperative-AI/frontend/src/components/HandoffModal.tsx)**:
   - Citizen modal dialog to confirm name, phone (optional), and PACS/village before generating the official slip.
2. **[`frontend/src/components/AssistanceSlipView.tsx`](file:///Users/pranav/SIH26088-Cooperative-AI/frontend/src/components/AssistanceSlipView.tsx)**:
   - Formats the 58mm thermal-style receipt on screen with QR code, reference ID, citizen query, translated officer note, AI advice, and official sources, with a "Print Slip" button.
3. **[`frontend/src/utils/qrGenerator.ts`](file:///Users/pranav/SIH26088-Cooperative-AI/frontend/src/utils/qrGenerator.ts)**:
   - Lightweight, standalone QR SVG generation utility.
4. **[`backend/scripts/test_human_handoff.py`](file:///Users/pranav/SIH26088-Cooperative-AI/backend/scripts/test_human_handoff.py)**:
   - Automated verification test suite for handoff creation, NMT translation, slip payload generation, and Admin visibility.

---

## 5. Current Grievance Flow vs Proposed Handoff Flow

| Stage | Current Grievance Flow (`GrievanceWorkflow.tsx`) | Proposed Human Handoff Flow (Phase 3A) |
| :--- | :--- | :--- |
| **Trigger** | Manual navigation to "Grievance" tab | Contextual CTA directly on any AI response card (Voice or Text) |
| **Data Source** | Citizen types everything from scratch | Pre-fills from active AI session (User Query, AI Guidance, Citations) |
| **Backend API** | **None** (purely client-side string formatter in React) | Calls `POST /api/grievance/handoff` |
| **Persistence** | None (lost on page reload) | Persists to Supabase `grievances` table linked to conversation UUID |
| **Multilingual** | Shows static UI strings | Translates citizen text via **Bhashini NMT** for non-native officers |
| **Reference Code** | None | Formats official reference ID (e.g. `PACS-2026-XXXX`) |
| **Physical Output** | `.txt` download only | Clean **58mm thermal slip layout** with browser print & QR code |
| **Admin Visibility** | Invisible (0 records in Admin) | **Immediately visible** in `/Users/pranav/Sarkar Setu Admin` |

---

## 6. PACS Context Availability

| Parameter | Status | Current Code Source | Phase 3A Utilization Plan |
| :--- | :--- | :--- | :--- |
| **`pacs_name`** | **EXISTS** in DB Schema & Admin | `grievances.pacs_name`, `kiosks.pacs_name` | Citizen confirms/edits PACS name; pre-filled if kiosk or location known. |
| **`pacs_id`** | **NOT FOUND** | Not present in DB or frontend | Use string `pacs_name` as canonical key (consistent with current Admin triage). |
| **`district` / `state`** | **EXISTS** in Location Service | `locationService.ts` (OSM reverse geocoding) | Pre-fills district in handoff dialog automatically from GPS. |
| **`kiosk_id`** | **EXISTS** in Backend Kiosks API | `backend/app/api/routes/kiosks.py` | Optional header/parameter passed if client is a physical kiosk. |
| **`citizen-selected PACS`** | **MOCK/DEMO ONLY** in Grievance UI | Text input in `GrievanceWorkflow.tsx` | Upgrade to standard input with local PACS suggestions (e.g. Dindori, Baramati). |
| **`Sahkaar ID`** | **NOT FOUND** | Does not exist in codebase | Do not invent; use reference ticket ID (e.g. `PACS-2026-XXXX`). |

---

## 7. MeitY Bhashini NMT Readiness

### Live Tested Capabilities (from Compatibility Report):
- **English → Hindi (EN → HI)**: Verified live (350.5 ms latency, 200 OK).
- **English → Marathi (EN → MR)**: Verified live (367.0 ms latency, 200 OK).
- **Hindi → English (HI → EN)**: Verified live (481.0 ms latency, 200 OK).
- **Marathi → English (MR → EN)**: Verified live (2,254 ms cold-start, ~380ms warm, 200 OK).

### Indic-to-Indic Translation Strategy (MR ↔ HI):
- Bhashini Dhruva pipeline accepts `sourceLanguage: "mr"`, `targetLanguage: "hi"` directly.
- **Failover Strategy**: If direct Indic-to-Indic returns non-200 or times out:
  1. Primary: Direct `MR → HI` or `HI → MR`.
  2. Fallback 1: Pivot translation `MR → EN → HI`.
  3. Fallback 2: Graceful non-blocking degradation (return original untranslated text with note: *"Original Citizen Language: Marathi"*).
- **Timeout**: 6.0s timeout per NMT call; never block ticket creation if translation fails.

---

## 8. QR Code Readiness & Recommendation

### Audit of Current Dependencies:
- `frontend/package.json` contains:
  ```json
  "dependencies": {
    "html2canvas": "^1.4.1",
    "jspdf": "^4.2.1",
    "react": "^19.2.8",
    "react-dom": "^19.2.8"
  }
  ```
- No QR library is currently installed.

### Technical Constraint:
- The project runs on **React 19 (`^19.2.8`)**.
- Older packages like `qrcode.react` (v3.x) specify peer dependency `react@"^16.8.0 || ^17.0.0 || ^18.0.0"`, causing `npm install` peer conflict errors or requiring `--legacy-peer-deps`.

### Recommended Solution:
**Zero-Dependency Pure TypeScript SVG QR Generator** or `qrcode` (core JS package):
- **Option A (Zero New Dependencies - Recommended)**:
  Create `frontend/src/utils/qrGenerator.ts` containing a self-contained, lightweight QR matrix generator function that renders pure inline SVG elements (`<svg viewBox="...">`). It requires **0 npm packages**, guarantees zero peer dependency conflicts with React 19, and adds 0 KB to `package.json`.
- **Option B**:
  `npm install qrcode @types/qrcode` (framework-agnostic JS library, works across all React versions).
- **QR Payload Content**:
  ```text
  https://sahkaarsetu.gov.in/verify/slip?ref=PACS-2026-0814&pacs=Dindori&cat=PMFBY
  ```

---

## 9. 58mm Thermal Slip Print Readiness

### How Browser Printing Works Without Hardware Drivers:
Thermal POS printers (58mm and 80mm) installed via USB, Bluetooth, or Network appear as standard printers in Windows, macOS, Linux, and Android.
By configuring CSS print media styles specifically for **58mm roll width (54mm printable area)**, clicking `window.print()` triggers the browser's native print sheet formatted for receipt rolls:

```css
@media print {
  @page {
    size: 58mm auto;
    margin: 0;
  }
  body * {
    visibility: hidden;
  }
  .assistance-slip-printable, .assistance-slip-printable * {
    visibility: visible;
  }
  .assistance-slip-printable {
    position: absolute;
    left: 0;
    top: 0;
    width: 52mm;
    margin: 0 3mm;
    font-family: 'Courier New', Courier, monospace;
    font-size: 11px;
    line-height: 1.3;
    color: #000;
  }
  .assistance-slip__qr svg {
    width: 38mm;
    height: 38mm;
    margin: 2mm auto;
    display: block;
  }
}
```

### Slip Content Layout:
```
================================
     SAHKAARSETU (सहकारसेतू)
   PACS ASSISTANCE REFERENCE SLIP
================================
Ref ID : PACS-2026-A8F29
Date   : 13-Sep-2026 15:30
PACS   : Dindori PACS (Nashik)
Category: PMFBY Crop Insurance
Citizen: Tukaram S. K****
Phone  : +91 98221 •••••
--------------------------------
[ CITIZEN QUERY / तक्रार ]
अवकाळी पावसामुळे कांद्याचे नुकसान
झाले असून ७२ तासांच्या आत भरपाई
मिळण्यासाठी काय करावे?

[ OFFICER NOTE (Translated EN) ]
Crop damage due to unseasonal
rain; urgent claim intimation.

[ GROUNDED AI GUIDANCE ]
1. Submit Annexure-IV notice to
   PACS Secretary within 72 hrs.
2. Attach 7/12 & 8A land records.
3. Obtain talathi inspection slip.

[ OFFICIAL SOURCES CITED ]
- PMFBY Operational Guidelines Cl.15
- Maharashtra Coop Societies Act S.91
--------------------------------
         [ QR CODE ]
  Scan to verify online ticket
--------------------------------
NOTICE: For facilitation at local
PACS desk. Official processing
subject to registrar verification.
================================
```

---

## 10. Admin Integration Readiness

### Verification of Existing Admin Grievance Architecture:
Inspecting [`backend/app/api/routes/admin_grievances.py`](file:///Users/pranav/SIH26088-Cooperative-AI/backend/app/api/routes/admin_grievances.py) and [`Sarkar Setu Admin/src/pages/GrievancesPage.tsx`](file:///Users/pranav/Sarkar%20Setu%20Admin/src/pages/GrievancesPage.tsx):

1. **Endpoint**: `GET /api/admin/grievances` reads directly from the `grievances` table.
2. **Filtering**: Admin already filters by `pacs_name`, `category`, `status`, and `priority`.
3. **Detail View**: When an Admin clicks a case, `GET /api/admin/grievances/{id}` returns:
   - `pacs_name`
   - `category`
   - `description` (Citizen summary)
   - `ai_guidance` (AI guidance + sources)
   - `conversation` (Full multi-turn transcript fetched via `conversation_id`!)
4. **Staff Workflow**: Extension officers can append verification notes (`POST /api/admin/grievances/{id}/notes`) and update status (`submitted` → `under_review` → `resolved`).

**Conclusion:** When `POST /api/grievance/handoff` writes to the `grievances` table, the case is **instantly visible in the Admin Portal without altering a single line of Admin code**.

---

## 11. Data Model Recommendation (Minimal Additive)

### Existing `grievances` Table Structure:
```sql
CREATE TABLE grievances (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id      UUID REFERENCES conversations(id) ON DELETE SET NULL,
    category             TEXT,
    description          TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'draft',
    priority             TEXT NOT NULL DEFAULT 'medium',
    assigned_staff       TEXT,
    pacs_name            TEXT,
    citizen_masked_name  TEXT DEFAULT 'Citizen (Protected)',
    citizen_phone_masked TEXT DEFAULT '+91 98******45',
    staff_notes          JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_guidance          TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Proposed Additive Fields (Optional / Backward Compatible):
To maintain strict backward compatibility without requiring database rebuilds:
1. `description`: Contains the citizen's original statement.
2. `ai_guidance`: Contains the combined grounded answer, source citations, and the **Bhashini translated summary for the officer**.
3. `category`: Intent classification (e.g. `PMFBY`, `PACS_SERVICE`, `COOPERATIVE_LAW`).
4. `pacs_name`: Selected or detected PACS society.
5. `status`: Initialized to `'submitted'`.
6. `priority`: Set to `'high'` for PMFBY/loan disputes, `'medium'` for general guidance.

*Optional Non-Breaking Migration (Phase 3A.1)*:
```sql
ALTER TABLE grievances 
  ADD COLUMN IF NOT EXISTS citizen_language TEXT DEFAULT 'mr',
  ADD COLUMN IF NOT EXISTS translated_summary TEXT,
  ADD COLUMN IF NOT EXISTS reference_code TEXT,
  ADD COLUMN IF NOT EXISTS source_citations JSONB DEFAULT '[]'::jsonb;
```
*(If the migration is not run, `repository.py` automatically preserves these fields in `ai_guidance` and in-memory fallbacks).*

---

## 12. Minimal Implementation Plan

The implementation is partitioned into 8 risk-controlled phases:

```
Phase A: Data & Repository Extension
  └─ File: backend/database/repository.py
  └─ Action: Add optional pacs_name, citizen_name, phone, ai_guidance to create_grievance().

Phase B: Handoff API Route Creation
  └─ File: backend/app/api/routes/grievance.py
  └─ Action: Add POST /api/grievance/handoff accepting HandoffCreateRequest.

Phase C: Bhashini NMT Integration
  └─ File: backend/app/api/routes/grievance.py
  └─ Action: Invoke bhashini_provider.translate_text() when citizen language differs from officer language.

Phase D: QR Generation Utility
  └─ File: frontend/src/utils/qrGenerator.ts
  └─ Action: Implement pure TypeScript SVG QR matrix generator.

Phase E: Printable 58mm Assistance Slip Component
  └─ File: frontend/src/components/AssistanceSlipView.tsx
  └─ Action: Component with receipt layout, print media CSS, and window.print() trigger.

Phase F: Citizen UI Integration
  └─ Files: frontend/src/components/HandoffModal.tsx, ChatMessage.tsx, VoiceModeView.tsx
  └─ Action: Add "Get Help from PACS" CTA on response cards; modal triggers handoff API.

Phase G: Admin Visibility Verification
  └─ Action: Verify newly generated handoff slip appears in Admin Grievances page with full transcript.

Phase H: Automated End-to-End Test Suite
  └─ File: backend/scripts/test_human_handoff.py
  └─ Action: 10 automated checks verifying API contract, NMT translation, slip generation, and Admin query.
```

---

## 13. Safety & Privacy Audit

1. **Citizen PII Protection**:
   - Contact phone numbers are automatically masked on the database level (`+91 98221 •••••`).
   - Physical receipts printed by the citizen display only the masked phone and initials (`Tukaram S. K****`) to prevent paper leakage in village centers.
2. **Secret Containment**:
   - `BHASHINI_API_KEY` and Supabase keys remain strictly server-side. The frontend only communicates with `POST /api/grievance/handoff`.
3. **No Fabricated PACS Entities**:
   - If location detection is denied or unavailable, `pacs_name` is set to `"Local PACS (Unspecified)"` with a prompt for the citizen to write their society name.
4. **Legal & Official Status Transparency**:
   - The printed receipt and modal display an unambiguous statutory notice:  
     `"DISCLAIMER: This document is a facilitation slip generated by SahkaarSetu for member guidance at your local PACS desk. It is not a court summons or official registrar order."`
5. **Translation Transparency**:
   - Translated notes are explicitly labeled: `"Officer Note: Machine translated via MeitY Bhashini NMT from Marathi"`.

---

## 14. Regression Protection Plan

To ensure zero unintended consequences across existing modules:
1. **Existing Routes Untouched**:
   - `POST /api/query` remains identical.
   - `POST /api/voice/transcribe` and `POST /api/voice/synthesize` remain identical.
   - Existing `POST /api/grievance` remains 100% backward-compatible.
2. **Existing Tests Must Pass 100%**:
   - `python3 backend/scripts/test_bhashini_voice_integration.py` (All 18 checks).
   - `python3 backend/scripts/test_citizen_regression.py` (All 6 checks).
   - `npm run build` in `frontend` (0 TypeScript errors).
3. **Zero Changes to Admin Codebase**:
   - No edits in `/Users/pranav/Sarkar Setu Admin`.

---

## 15. Explicit List of Files that MUST NOT Be Touched

The following files are strictly out of scope and **MUST NOT BE MODIFIED**:

```
1. /Users/pranav/Sarkar Setu Admin/* (Entire Admin codebase)
2. backend/rag/intent.py
3. backend/rag/router.py
4. backend/rag/retriever.py
5. backend/rag/pipeline.py
6. backend/rag/embeddings.py
7. backend/rag/prompts.py
8. backend/rag/validator.py
9. backend/rag/web_search.py
10. backend/rag/session_state.py
11. backend/app/providers/gemini_provider.py
12. backend/app/providers/groq_provider.py
13. backend/app/providers/ollama_provider.py
14. backend/app/providers/stt_provider.py
15. backend/app/schemas/query.py
16. backend/app/api/routes/query.py
17. backend/app/api/routes/voice.py
18. backend/app/api/routes/vision.py
19. backend/app/api/routes/health.py
20. backend/app/api/routes/knowledge.py
21. backend/app/api/routes/conversations.py
22. backend/app/api/routes/kiosks.py
23. frontend/src/i18n/* (All locales)
```

---

## 16. Final Verdict

# READY — MINIMAL ADDITIVE IMPLEMENTATION

The codebase and database architecture are completely ready for Citizen Phase 3A ("Get Help from PACS" / Multilingual Human Handoff). All core infrastructure—including MeitY Bhashini NMT translation, the Supabase `grievances` schema, the Admin triage portal, and browser thermal print formatting—already exists and can be composed via clean, additive extensions without risking any regression to the governed RAG, voice, or Admin systems.
