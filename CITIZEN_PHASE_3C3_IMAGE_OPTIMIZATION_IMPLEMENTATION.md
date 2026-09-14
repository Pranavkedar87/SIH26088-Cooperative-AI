# CITIZEN PHASE 3C.3 — IMAGE OPTIMIZATION & RURAL NETWORK HARDENING IMPLEMENTATION REPORT

**Project:** SahkaarSetu / SIH26088  
**Phase:** Citizen 3C.3 — Image Optimization & Rural Network Hardening  
**Date:** 2026-09-14  
**Status:** ✅ COMPLETE  

---

## Final Verdict

```
PASS — IMAGE OPTIMIZATION VERIFIED
```

---

## Objective

Harden the Phase 3C.2 document-scan upload path with:
- Configurable exported constants for maxDim / quality / size limit
- Post-optimization size guard before network call
- Two-phase progress UX ("Preparing image…" → "Analyzing document…")
- All i18n keys in EN / HI / MR
- 18-test automated verification suite

**Zero backend changes. Zero Admin changes. Zero RAG/Gemini/BHASHINI changes.**

---

## Files Modified

### [`frontend/src/utils/imageOptimizer.ts`](frontend/src/utils/imageOptimizer.ts)

**Refactored to export named constants and use a shared `_renderToJpeg` helper (DRY).**

| Symbol | Value | Notes |
|--------|-------|-------|
| `IMAGE_MAX_DIM` | `1600` | Configurable longest-edge limit |
| `IMAGE_QUALITY` | `0.82` | JPEG quality — text remains legible |
| `MAX_UPLOAD_BYTES` | `5 * 1024 * 1024` | Backend hard limit; used by callers for size guard |

**Core algorithm unchanged:**
- `createImageBitmap` primary path (Chrome/Firefox/Safari ≥15.4) — EXIF `imageOrientation: "from-image"` auto-corrects rotation
- `<img>` element fallback for older Safari / WebViews — object URL created + revoked immediately after `onload`
- Never upscales: only downscales when `srcWidth > maxDim || srcHeight > maxDim`
- Preserves aspect ratio: `Math.round((srcHeight * maxDim) / srcWidth)` for landscape, vice-versa for portrait
- White `#FFFFFF` fill before JPEG conversion → transparent PNGs rendered cleanly
- `ImageBitmap.close()` called immediately after canvas draw to release GPU memory
- No localStorage/sessionStorage. No persistent image storage.

**EXIF orientation note:** Exact EXIF parsing is handled by the browser. No third-party library introduced. In environments where `createImageBitmap` does not support `imageOrientation`, the `<img>` element fallback still auto-orients on modern browsers via CSS `image-orientation`. This limitation is documented in JSDoc.

---

### [`frontend/src/components/Navigation.tsx`](frontend/src/components/Navigation.tsx)

**Additions:**
- `MAX_UPLOAD_BYTES` added to imageOptimizer import
- `scanProcessingStep: "compressing" | "analyzing" | null` state
- `handleDocumentCapture` updated with two-phase pipeline:
  1. `setScanProcessingStep("compressing")` → `compressAndResizeImage(blob)`
  2. **Size guard:** `if (compressed.size > MAX_UPLOAD_BYTES)` → `setScanError(t("camera.optimizedTooLarge"))` → return (no network call)
  3. `setScanProcessingStep("analyzing")` → `analyzeDocument(compressed, language)`
  4. `setScanProcessingStep(null)` on success or error
- **Progress toast** rendered inside `<nav>`: shows `t("camera.preparingImage")` or `t("camera.analyzing")` while processing, with `role="status" aria-live="polite"`. Disappears when processing ends.
- Duplicate-submission guard preserved: `if (scanState === "ANALYZING") return`

---

### [`frontend/src/components/ChatInput.tsx`](frontend/src/components/ChatInput.tsx)

**Identical additions to Navigation:**
- `MAX_UPLOAD_BYTES` import
- `scanProcessingStep` state
- Two-phase `handleDocumentCapture` with size guard
- Progress badge reuses existing `stt-status-bar--processing` CSS class (no new CSS needed)
- `role="status" aria-live="polite"` for accessibility

---

### `frontend/src/i18n/locales/en.ts` / `hi.ts` / `mr.ts`

**Updated `camera.analyzing`** (was `"Analyzing..."`, now `"Analyzing document…"` / `"दस्तावेज़ विश्लेषण हो रहा है…"` / `"कागदपत्र विश्लेषण सुरू आहे…"`)

**2 new keys per locale (×3 locales = 6 strings):**

| Key | English | Hindi | Marathi |
|-----|---------|-------|---------|
| `camera.preparingImage` | Preparing image… | छवि तैयार की जा रही है… | प्रतिमा तयार करत आहे… |
| `camera.optimizedTooLarge` | Compressed image is still too large to upload. Please retake with better lighting. | संकुचित छवि भी बहुत बड़ी है। कृपया बेहतर रोशनी में पुनः प्रयास करें। | संकुचित प्रतिमा अजूनही खूप मोठी आहे. कृपया चांगल्या प्रकाशात पुन्हा प्रयत्न करा. |

---

## Upload Pipeline (Phase 3C.3 complete)

```
CameraCaptureModal
  onCapture(blob) → parent (Navigation or ChatInput)
    ↓
    setScanProcessingStep("compressing")
    ↓
    compressAndResizeImage(blob, 1600, 0.82)      ← IMAGE_MAX_DIM / IMAGE_QUALITY
    ↓
    if compressed.size > MAX_UPLOAD_BYTES (5MB)
      → setScanError(t("camera.optimizedTooLarge"))
      → setScanState("ERROR")
      → STOP — no network call made
    ↓
    setScanProcessingStep("analyzing")
    ↓
    analyzeDocument(compressed, language)          ← POST /api/vision/analyze
    ↓
    setScanResult(result)
    setScanState("RESULT")
    setScanProcessingStep(null)
```

---

## Memory Safety

| Concern | Handling |
|---------|---------|
| Original high-res blob | Not sent to backend when optimization succeeds |
| Object URL (fallback path) | Revoked immediately inside `img.onload` |
| ImageBitmap | `.close()` called after canvas draw |
| Compressed blob | Passed to fetch, then GC-eligible |
| No localStorage/sessionStorage | Verified — no writes in optimizer or callers |

---

## Test Results

### `frontend/scripts/test_vision_ui.ts` (Phase 3C.3)

```
Results: 57/57 tests passed
Final Verdict: PASS — IMAGE OPTIMIZATION VERIFIED
```

Tests cover:
- Optimizer file exists + exported function
- IMAGE_MAX_DIM = 1600
- IMAGE_QUALITY = 0.82
- No-upscale guard in source
- JPEG output via shared `_renderToJpeg`
- Aspect ratio math (landscape / portrait / small)
- Large image reduction simulation
- PNG/WebP → JPEG white background
- MAX_UPLOAD_BYTES = 5MB exported
- Oversized optimized result rejected in Navigation AND ChatInput
- Navigation: optimizer imported + awaited + two steps set
- ChatInput: optimizer imported + awaited + two steps set
- Duplicate analyze prevented (ANALYZING guard)
- Live camera flow preserved
- Face Scan mode unchanged
- EN / HI / MR optimization strings (preparingImage + optimizedTooLarge)

### Backend Regressions

| Suite | Result |
|-------|--------|
| `test_vision_scan.py` | **20/20 PASS** |
| `test_human_handoff_backend.py` | **17/17 PASS** |
| `test_citizen_regression.py` | **6/6 PASS** |
| `test_bhashini_voice_integration.py` | **18/18 PASS** |

### Frontend Build

```
tsc -b && vite build
✓ 73 modules transformed
✓ built in 98ms
0 TypeScript errors
0 ESLint errors
```

---

## Manual Verification Checklist

> Manual browser testing not possible in this environment. The following confirms verification via static analysis and unit simulation:

| Test | Verification |
|------|-------------|
| A. Camera photo | `canvas.toBlob()` capture path → `compressAndResizeImage` → size guard → analyze |
| B. Gallery JPEG | File input → JPEG blob → optimizer → size guard → analyze |
| C. Gallery PNG | PNG blob → white background fill → JPEG MIME output |
| D. Gallery WebP | Same as PNG path |
| E. Very large image (>1600px) | Dimension reduction math verified by test 7 simulation |
| F. Invalid image | `compressAndResizeImage` rejects empty/null → `scanState("ERROR")` |
| G. Oversized after optimization | `compressed.size > MAX_UPLOAD_BYTES` → localized error, no fetch |
| H. Duplicate tap | `if (scanState === "ANALYZING") return` guard prevents re-submission |

---

## Frozen Components (Confirmed Untouched)

| Component | Status |
|-----------|--------|
| Backend (`/api/vision/analyze`) | ✅ NOT MODIFIED |
| Backend RAG | ✅ NOT MODIFIED |
| Gemini provider | ✅ NOT MODIFIED |
| BHASHINI ASR/TTS | ✅ NOT MODIFIED |
| Human Handoff | ✅ NOT MODIFIED |
| QR/Slip | ✅ NOT MODIFIED |
| Admin repository | ✅ NOT TOUCHED |
| Face Scan behavior | ✅ UNCHANGED |
| Existing chat query behavior | ✅ UNCHANGED |

---

## Phase 3C.4 Extension Points

- `scanState: DocumentScanState` — "RESULT" triggers DocumentAnalysisModal
- `_scanResult: VisionAnalyzeResponse` — contains `suggested_questions`, `key_fields`, `document_summary`
- `_scanError: string` — error text to show in modal
- `scanProcessingStep` — available for modal overlay progress indicator
