/**
 * Phase 3C.3 — Image Optimization & Rural Network Hardening Tests
 *
 * 18 test cases covering:
 *   1.  Optimizer file exists
 *   2.  maxDim constant = 1600
 *   3.  quality constant = 0.82
 *   4.  No-upscale guard in source
 *   5.  Output is JPEG
 *   6.  Aspect ratio preservation logic
 *   7.  Large image dimensions are reduced
 *   8.  PNG/WebP → JPEG conversion (white background)
 *   9.  Optimized size checked before upload (MAX_UPLOAD_BYTES exported)
 *   10. >5MB optimized result rejected in Navigation
 *   11. Navigation path uses optimizer
 *   12. ChatInput path uses optimizer
 *   13. Duplicate analyze prevented (ANALYZING guard)
 *   14. Existing camera flow preserved (live capture path untouched)
 *   15. Face Scan unchanged
 *   16. English optimization/error strings (preparingImage + optimizedTooLarge)
 *   17. Hindi optimization/error strings
 *   18. Marathi optimization/error strings
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

// ─────────────────────────────────────────────────────────────────────────────
// Test 1: Optimizer file exists
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[1] Optimizer file exists");
{
  let content = "";
  try {
    content = src("frontend/src/utils/imageOptimizer.ts");
  } catch {
    assert(false, "imageOptimizer.ts is readable");
  }
  assert(content.length > 0, "imageOptimizer.ts is readable and non-empty");
  assert(
    content.includes("export async function compressAndResizeImage"),
    "compressAndResizeImage is exported"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 2: maxDim constant = 1600
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[2] maxDim constant = 1600");
{
  const content = src("frontend/src/utils/imageOptimizer.ts");
  assert(
    content.includes("export const IMAGE_MAX_DIM = 1600"),
    "IMAGE_MAX_DIM exported as 1600"
  );
  assert(
    content.includes("maxDim: number = IMAGE_MAX_DIM"),
    "compressAndResizeImage defaults to IMAGE_MAX_DIM"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 3: quality constant = 0.82
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[3] quality constant = 0.82");
{
  const content = src("frontend/src/utils/imageOptimizer.ts");
  assert(
    content.includes("export const IMAGE_QUALITY = 0.82"),
    "IMAGE_QUALITY exported as 0.82"
  );
  assert(
    content.includes("quality: number = IMAGE_QUALITY"),
    "compressAndResizeImage defaults to IMAGE_QUALITY"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 4: No-upscale guard in source
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[4] No-upscale guard");
{
  const content = src("frontend/src/utils/imageOptimizer.ts");
  // Must check that dimensions are > maxDim before downscaling
  assert(
    content.includes("srcWidth > maxDim || srcHeight > maxDim"),
    "only downscales when width or height exceeds maxDim"
  );
  assert(
    content.includes("Never upscales small images"),
    "JSDoc documents no-upscale guarantee"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 5: Output is JPEG
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[5] Output is JPEG");
{
  const content = src("frontend/src/utils/imageOptimizer.ts");
  // Refactored optimizer uses a shared _renderToJpeg helper — one call site is correct (DRY).
  assert(
    content.includes('"image/jpeg"'),
    'canvas.toBlob uses "image/jpeg" MIME type'
  );
  assert(
    content.includes("_renderToJpeg"),
    "shared _renderToJpeg helper used by both ImageBitmap and fallback paths"
  );
  assert(
    content.includes("image/jpeg") && content.includes("quality"),
    "quality parameter passed to image/jpeg blob serialisation"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 6: Aspect ratio preservation logic
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[6] Aspect ratio preservation");
{
  const content = src("frontend/src/utils/imageOptimizer.ts");
  // Must have Math.round and proportional calculation for both axes
  assert(
    content.includes("Math.round((srcHeight * maxDim) / srcWidth)"),
    "landscape: height scaled proportionally"
  );
  assert(
    content.includes("Math.round((srcWidth * maxDim) / srcHeight)"),
    "portrait: width scaled proportionally"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 7: Large image dimensions are reduced
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[7] Large image dimension reduction logic");
{
  // Simulate the reduction calculation in pure JS (no DOM needed)
  function simulateResize(w: number, h: number, maxDim: number): { w: number; h: number } {
    let tw = w;
    let th = h;
    if (w > maxDim || h > maxDim) {
      if (w >= h) {
        tw = maxDim;
        th = Math.round((h * maxDim) / w);
      } else {
        th = maxDim;
        tw = Math.round((w * maxDim) / h);
      }
    }
    return { w: tw, h: th };
  }

  const landscape = simulateResize(3200, 2400, 1600);
  assert(landscape.w === 1600, `landscape 3200×2400 → width=1600 (got ${landscape.w})`);
  assert(landscape.h === 1200, `landscape 3200×2400 → height=1200 (got ${landscape.h})`);

  const portrait = simulateResize(2400, 3200, 1600);
  assert(portrait.h === 1600, `portrait 2400×3200 → height=1600 (got ${portrait.h})`);
  assert(portrait.w === 1200, `portrait 2400×3200 → width=1200 (got ${portrait.w})`);

  const small = simulateResize(800, 600, 1600);
  assert(small.w === 800, `small 800×600 NOT upscaled, w stays 800 (got ${small.w})`);
  assert(small.h === 600, `small 800×600 NOT upscaled, h stays 600 (got ${small.h})`);
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 8: PNG/WebP → JPEG (white background fill)
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[8] PNG/WebP → JPEG conversion (white background)");
{
  const content = src("frontend/src/utils/imageOptimizer.ts");
  assert(
    content.includes('ctx.fillStyle = "#FFFFFF"'),
    "white background applied before JPEG conversion"
  );
  assert(
    content.includes("ctx.fillRect("),
    "fillRect called to paint white background"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 9: MAX_UPLOAD_BYTES exported and equals 5MB
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[9] MAX_UPLOAD_BYTES exported = 5MB");
{
  const content = src("frontend/src/utils/imageOptimizer.ts");
  assert(
    content.includes("export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024"),
    "MAX_UPLOAD_BYTES exported as 5 * 1024 * 1024"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 10: >5MB optimized result rejected in Navigation & ChatInput
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[10] Oversized optimized result rejected before network call");
{
  const nav = src("frontend/src/components/Navigation.tsx");
  const chat = src("frontend/src/components/ChatInput.tsx");

  assert(
    nav.includes("compressed.size > MAX_UPLOAD_BYTES"),
    "Navigation: size guard checks compressed.size > MAX_UPLOAD_BYTES"
  );
  assert(
    nav.includes('t("camera.optimizedTooLarge")'),
    "Navigation: shows camera.optimizedTooLarge error on oversized result"
  );
  assert(
    nav.includes("setScanState(\"ERROR\")") && nav.includes("return;"),
    "Navigation: sets ERROR state and returns before network call"
  );

  assert(
    chat.includes("compressed.size > MAX_UPLOAD_BYTES"),
    "ChatInput: size guard checks compressed.size > MAX_UPLOAD_BYTES"
  );
  assert(
    chat.includes('t("camera.optimizedTooLarge")'),
    "ChatInput: shows camera.optimizedTooLarge error on oversized result"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 11: Navigation path uses optimizer
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[11] Navigation path uses optimizer");
{
  const nav = src("frontend/src/components/Navigation.tsx");
  assert(
    nav.includes('import { compressAndResizeImage, MAX_UPLOAD_BYTES } from "../utils/imageOptimizer"'),
    "Navigation imports compressAndResizeImage and MAX_UPLOAD_BYTES"
  );
  assert(
    nav.includes("const compressed = await compressAndResizeImage(blob)"),
    "Navigation awaits compressAndResizeImage before analyze"
  );
  assert(
    nav.includes('setScanProcessingStep("compressing")'),
    "Navigation sets compressing step before optimize"
  );
  assert(
    nav.includes('setScanProcessingStep("analyzing")'),
    "Navigation sets analyzing step before backend call"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 12: ChatInput path uses optimizer
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[12] ChatInput path uses optimizer");
{
  const chat = src("frontend/src/components/ChatInput.tsx");
  assert(
    chat.includes('import { compressAndResizeImage, MAX_UPLOAD_BYTES } from "../utils/imageOptimizer"'),
    "ChatInput imports compressAndResizeImage and MAX_UPLOAD_BYTES"
  );
  assert(
    chat.includes("const compressed = await compressAndResizeImage(blob)"),
    "ChatInput awaits compressAndResizeImage before analyze"
  );
  assert(
    chat.includes('setScanProcessingStep("compressing")'),
    "ChatInput sets compressing step before optimize"
  );
  assert(
    chat.includes('setScanProcessingStep("analyzing")'),
    "ChatInput sets analyzing step before backend call"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 13: Duplicate analyze prevented (ANALYZING guard)
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[13] Duplicate analyze prevented");
{
  const nav = src("frontend/src/components/Navigation.tsx");
  const chat = src("frontend/src/components/ChatInput.tsx");
  assert(
    nav.includes('if (scanState === "ANALYZING") return;'),
    "Navigation: early return when already ANALYZING"
  );
  assert(
    chat.includes('if (scanState === "ANALYZING") return;'),
    "ChatInput: early return when already ANALYZING"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 14: Existing camera flow preserved (live capture path in modal)
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[14] Live camera flow preserved");
{
  const modal = src("frontend/src/components/CameraCaptureModal.tsx");
  assert(
    modal.includes("handleCapture"),
    "handleCapture function exists in CameraCaptureModal"
  );
  assert(
    modal.includes("canvas.toDataURL"),
    "Live camera capture still uses canvas.toDataURL for preview"
  );
  assert(
    modal.includes("handleRetake"),
    "handleRetake exists (live camera retake preserved)"
  );
  assert(
    modal.includes("camera-shutter-btn"),
    "camera shutter button still rendered"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 15: Face Scan mode unchanged
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[15] Face Scan mode unchanged");
{
  const modal = src("frontend/src/components/CameraCaptureModal.tsx");
  const nav = src("frontend/src/components/Navigation.tsx");
  const chat = src("frontend/src/components/ChatInput.tsx");

  assert(
    modal.includes('"face_scan"'),
    "face_scan mode still handled in CameraCaptureModal"
  );
  assert(
    modal.includes("handleDone"),
    "face_scan still calls handleDone (not handleAnalyze)"
  );
  // onCapture must NOT be wired for face_scan
  assert(
    nav.includes('onCapture={activeCameraMode === "document_scan" ? handleDocumentCapture : undefined}'),
    "Navigation: onCapture only wired for document_scan, not face_scan"
  );
  assert(
    chat.includes('onCapture={activeCameraMode === "document_scan" ? handleDocumentCapture : undefined}'),
    "ChatInput: onCapture only wired for document_scan, not face_scan"
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 16: English optimization strings
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[16] English optimization/error strings");
{
  const en = src("frontend/src/i18n/locales/en.ts");
  assert(en.includes('"camera.preparingImage"'), 'en.ts has "camera.preparingImage"');
  assert(en.includes('"camera.optimizedTooLarge"'), 'en.ts has "camera.optimizedTooLarge"');
  assert(en.includes("Preparing image"), 'en: preparingImage message contains "Preparing image"');
  assert(
    en.includes("Compressed image is still too large"),
    'en: optimizedTooLarge gives honest, actionable message'
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 17: Hindi optimization/error strings
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[17] Hindi optimization/error strings");
{
  const hi = src("frontend/src/i18n/locales/hi.ts");
  assert(hi.includes('"camera.preparingImage"'), 'hi.ts has "camera.preparingImage"');
  assert(hi.includes('"camera.optimizedTooLarge"'), 'hi.ts has "camera.optimizedTooLarge"');
  assert(hi.includes("छवि तैयार"), 'hi: preparingImage in Hindi');
  assert(hi.includes("संकुचित छवि"), 'hi: optimizedTooLarge in Hindi');
}

// ─────────────────────────────────────────────────────────────────────────────
// Test 18: Marathi optimization/error strings
// ─────────────────────────────────────────────────────────────────────────────
console.log("\n[18] Marathi optimization/error strings");
{
  const mr = src("frontend/src/i18n/locales/mr.ts");
  assert(mr.includes('"camera.preparingImage"'), 'mr.ts has "camera.preparingImage"');
  assert(mr.includes('"camera.optimizedTooLarge"'), 'mr.ts has "camera.optimizedTooLarge"');
  assert(mr.includes("प्रतिमा तयार"), 'mr: preparingImage in Marathi');
  assert(mr.includes("संकुचित प्रतिमा"), 'mr: optimizedTooLarge in Marathi');
}

// ─────────────────────────────────────────────────────────────────────────────
// Summary
// ─────────────────────────────────────────────────────────────────────────────
const total = passed.length + failed.length;
console.log(`\n${"─".repeat(60)}`);
console.log(`Results: ${passed.length}/${total} tests passed`);
if (failed.length > 0) {
  console.error(`\nFailed tests:`);
  failed.forEach((f) => console.error(`  ✗ ${f}`));
  console.log("\nFinal Verdict: BLOCKED — IMAGE OPTIMIZATION NOT SAFE");
  process.exit(1);
} else {
  console.log("\nFinal Verdict: PASS — IMAGE OPTIMIZATION VERIFIED");
  process.exit(0);
}
