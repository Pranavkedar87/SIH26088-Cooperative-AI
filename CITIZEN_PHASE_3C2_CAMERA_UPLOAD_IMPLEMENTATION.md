# CITIZEN PHASE 3C.2 — CAMERA & GALLERY UPLOAD WIRING IMPLEMENTATION REPORT

**Project:** SahkaarSetu / SIH26088  
**Phase:** Citizen 3C.2 — Camera & Gallery Upload Wiring  
**Date:** 2026-09-14  
**Status:** ✅ COMPLETE  

---

## Final Verdict

```
PASS — CAMERA & UPLOAD WIRING VERIFIED
```

---

## Objective

Wire the existing Citizen camera UI to the verified `POST /api/vision/analyze` backend endpoint.  
Add mobile gallery/file upload fallback.  
**No backend changes. No RAG changes. No BHASHINI changes. No Admin changes.**

---

## Files Modified

### `frontend/src/api/client.ts`
- Added `analyzeDocument(imageBlob: Blob, language?: string): Promise<VisionAnalyzeResponse>`
- Uses `FormData` with `multipart/form-data` — Content-Type NOT manually set (browser auto-sets boundary)
- Appends `file` (named `document.jpg`) and `language` to form
- 60-second AbortController timeout (same pattern as other API calls)
- Endpoint: `POST /api/vision/analyze`
- Throws on non-OK responses with backend detail message

### `frontend/src/components/CameraCaptureModal.tsx` (full rewrite, functionally additive)
**New prop:** `onCapture?: (blob: Blob) => void`  
**New features (document_scan mode only):**
- Privacy notice banner ("Image used only for document analysis. Not stored.")
- Gallery/file picker `<input type="file">` (hidden, triggered by button) — JPEG/PNG/WebP only
- Gallery upload button in live camera controls row (🖼️ icon)
- File size validation: rejects files > 5MB with i18n error message
- MIME type validation: rejects non-image files with i18n error message
- Permission-denied fallback: when camera permission denied in document_scan mode → shows "Upload from Gallery" fullscreen fallback instead of red error
- `capturedBlobRef`: stores captured/uploaded Blob (useRef — no re-render)
- Canvas capture now also calls `canvas.toBlob()` to store Blob (in addition to dataURL for preview)
- After capture/upload: "Analyze Document" button replaces "Done" (only when `onCapture` provided)
- `handleAnalyze()`: calls `onCapture(blob)` then `onClose()` — parent owns API call
- `handleRetake()`: clears preview + blob, respects permission-denied state
**Face-scan mode:** completely unchanged — "Done" button still calls `onClose()`

### `frontend/src/components/Navigation.tsx`
- Added imports: `DocumentScanState`, `VisionAnalyzeResponse`, `analyzeDocument`, `compressAndResizeImage`
- Added `scanState`, `_scanResult`, `_scanError` state (DocumentScanState machine)
- Added `handleDocumentCapture(blob: Blob)` — async, compresses → calls analyzeDocument → updates state
- Added `onCapture` prop to `CameraCaptureModal` wired only for `document_scan` mode
- Extension point: Phase 3C.3 will consume `_scanResult` state to show DocumentAnalysisModal

### `frontend/src/components/ChatInput.tsx`
- Same additions as Navigation.tsx (ChatInput is an independent camera entry point)
- `handleDocumentCapture` identical pattern
- `onCapture` wired only for `document_scan` mode

### `frontend/src/i18n/locales/en.ts` / `hi.ts` / `mr.ts`
**10 new keys added to all 3 locales:**
| Key | English | Hindi | Marathi |
|-----|---------|-------|---------|
| `camera.uploadGallery` | Upload from Gallery | गैलरी से अपलोड करें | गॅलरीतून अपलोड करा |
| `camera.analyze` | Analyze Document | दस्तावेज़ विश्लेषण करें | कागदपत्र विश्लेषण करा |
| `camera.analyzing` | Analyzing... | विश्लेषण हो रहा है... | विश्लेषण सुरू आहे... |
| `camera.privacyNotice` | Image used only for document analysis... | छवि केवल दस्तावेज़ विश्लेषण के लिए... | प्रतिमा केवळ कागदपत्र विश्लेषणासाठी... |
| `camera.identityRefused` | Identity documents not processed... | पहचान दस्तावेज़ गोपनीयता के कारण... | गोपनीयतेसाठी ओळख कागदपत्रे... |
| `camera.retakeOrChoose` | Retake or Choose Another | पुनः लें या दूसरी छवि चुनें | पुन्हा घ्या किंवा दुसरी... |
| `camera.analysisFailed` | Document analysis failed... | दस्तावेज़ विश्लेषण विफल रहा... | कागदपत्र विश्लेषण अयशस्वी... |
| `camera.fileTooBig` | Image file is too large (max 5MB) | छवि फ़ाइल बहुत बड़ी है... | प्रतिमा फाइल खूप मोठी आहे... |
| `camera.unsupportedFormat` | Please use JPEG, PNG or WebP format | कृपया JPEG, PNG या WebP... | कृपया JPEG, PNG किंवा WebP... |
| `camera.permissionFallback` | Camera unavailable. Please upload from gallery | कैमरा उपलब्ध नहीं... | कॅमेरा उपलब्ध नाही... |

---

## Files Created

### `frontend/scripts/test_vision_ui.ts`
- 63 test assertions across 8 test groups
- Tests: DocumentScanState types, VisionAnalyzeResponse shape, analyzeDocument API signature, CameraCaptureModal prop contract, Navigation state machine, ChatInput state machine, i18n completeness (3 locales × 10 keys = 30 checks), imageOptimizer utility

---

## Architecture: Data Flow

```
CameraCaptureModal (document_scan + onCapture prop)
  │
  ├── Camera capture → canvas.toBlob() → capturedBlobRef
  ├── Gallery upload → file.type/size validation → capturedBlobRef
  └── "Analyze Document" button → onCapture(blob) → onClose()
                ↓
  Navigation / ChatInput (parent owns network)
    ├── compressAndResizeImage(blob) → compressed Blob (~250KB)
    ├── analyzeDocument(compressed, language) → POST /api/vision/analyze
    ├── scanState: READY → ANALYZING → RESULT | ERROR
    └── _scanResult: VisionAnalyzeResponse (Phase 3C.3 extension point)
```

**Key design decisions:**
- Modal is decoupled from network — blob flows to parent before API call
- No immediate upload after capture — citizen must tap "Analyze Document"
- `capturedBlobRef` is a `useRef` (no re-render on blob assignment)
- `compressAndResizeImage` runs before every upload (mobile photo optimization)
- Face-scan mode: 100% unchanged behavior

---

## Test Results

| Test Suite | Result |
|-----------|--------|
| `test_vision_ui.ts` (frontend) | 63/63 PASS |
| `test_human_handoff_backend.py` | 17/17 PASS |
| `npm run build` (TypeScript + Vite) | ✅ 0 errors, 92ms |

**Pre-existing failures (not caused by Phase 3C.2):**
- `test_handoff_slip.ts` and `test_handoff_ui.ts` — crash on wrong path `src/types/index.ts` instead of `frontend/src/types/index.ts` (pre-existing bug from Phase 3A.3 era)

---

## Safety Confirmation

| Constraint | Status |
|-----------|--------|
| Backend unmodified | ✅ |
| `/api/vision/analyze` unmodified | ✅ |
| `/api/vision/query` unmodified | ✅ |
| RAG unmodified | ✅ |
| Gemini provider unmodified | ✅ |
| BHASHINI unmodified | ✅ |
| Human Handoff unmodified | ✅ |
| QR/slip unmodified | ✅ |
| Admin repository untouched | ✅ |
| Existing chat query behavior preserved | ✅ |
| Face-scan mode behavior preserved | ✅ |

---

## Phase 3C.3 Extension Points

The following are ready for Phase 3C.3 (Document Analysis UI):
- `_scanResult: VisionAnalyzeResponse | null` state in Navigation + ChatInput
- `_scanError: string | null` state in Navigation + ChatInput  
- `scanState: DocumentScanState` machine in Navigation + ChatInput
- `suggested_questions[]` from VisionAnalyzeResponse ready for question chip rendering
- `document_summary` and `key_fields` ready for structured display
- `refusal_reason` (identity guard) ready for user messaging
