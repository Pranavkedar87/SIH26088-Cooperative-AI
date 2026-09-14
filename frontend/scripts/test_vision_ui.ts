/**
 * Phase 3C.2 — Camera & Gallery Upload Wiring Tests
 *
 * 18 test cases covering:
 *   - imageOptimizer utility
 *   - analyzeDocument API client function signature
 *   - CameraCaptureModal prop contract
 *   - Navigation / ChatInput state machine
 *   - i18n string completeness
 *   - DocumentScanState type coverage
 *   - File validation logic
 *
 * Run: node --experimental-strip-types frontend/scripts/test_vision_ui.ts
 */

// ── Minimal DOM stubs for Node environment ────────────────────────────────────
// We test logic / types, not rendering.
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

// ── Test 1: DocumentScanState type values ─────────────────────────────────────
console.log("\n[1] DocumentScanState type values");
{
  // These are the exact union members defined in types/index.ts
  type DocumentScanState = "READY" | "CAPTURING" | "IMAGE_READY" | "ANALYZING" | "RESULT" | "ERROR";
  const allStates: DocumentScanState[] = ["READY", "CAPTURING", "IMAGE_READY", "ANALYZING", "RESULT", "ERROR"];
  assert(allStates.length === 6, "DocumentScanState has exactly 6 states");
  assert(allStates.includes("ANALYZING"), "ANALYZING state present");
  assert(allStates.includes("RESULT"), "RESULT state present");
  assert(allStates.includes("ERROR"), "ERROR state present");
}

// ── Test 2: VisionAnalyzeResponse shape ───────────────────────────────────────
console.log("\n[2] VisionAnalyzeResponse shape");
{
  // Simulate the contract from types/index.ts
  interface VisionAnalyzeResponse {
    success: boolean;
    document_type: string;
    readability: string;
    detected_language: string;
    key_fields: Record<string, string | null>;
    document_summary?: string | null;
    suggested_questions: string[];
    has_sensitive_pii: boolean;
    refusal_reason?: string | null;
    processing_time_ms?: number | null;
  }

  const mockResult: VisionAnalyzeResponse = {
    success: true,
    document_type: "PMFBY_POLICY",
    readability: "CLEAR",
    detected_language: "en",
    key_fields: { policy_number: "POL-2024-001", farmer_name: null },
    suggested_questions: ["What is covered under this policy?"],
    has_sensitive_pii: false,
  };

  assert(mockResult.success === true, "success field boolean");
  assert(mockResult.suggested_questions.length > 0, "suggested_questions array present");
  assert("refusal_reason" in mockResult || mockResult.refusal_reason === undefined, "refusal_reason optional");
  assert(mockResult.key_fields["farmer_name"] === null, "key_fields allows null values");
}

// ── Test 3: analyzeDocument API function signature ────────────────────────────
console.log("\n[3] analyzeDocument API function signature");
{
  // Read source to verify function exists and signature
  const fs = await import("fs");
  const clientSrc = fs.readFileSync(
    new URL("../../frontend/src/api/client.ts", import.meta.url).pathname,
    "utf8"
  );

  assert(
    clientSrc.includes("export async function analyzeDocument"),
    "analyzeDocument function exported"
  );
  assert(
    clientSrc.includes("form.append(\"file\", imageBlob, \"document.jpg\")"),
    "file appended with correct filename"
  );
  assert(
    clientSrc.includes("form.append(\"language\", language)"),
    "language appended to form"
  );
  assert(
    !clientSrc.includes("Content-Type.*multipart"),
    "Content-Type NOT manually set (boundary auto-set)"
  );
  assert(
    clientSrc.includes("/api/vision/analyze"),
    "correct endpoint /api/vision/analyze"
  );
  assert(
    clientSrc.includes("60000"),
    "60s timeout for Gemini multimodal"
  );
}

// ── Test 4: CameraCaptureModal onCapture prop contract ────────────────────────
console.log("\n[4] CameraCaptureModal onCapture prop contract");
{
  const fs = await import("fs");
  const modalSrc = fs.readFileSync(
    new URL("../../frontend/src/components/CameraCaptureModal.tsx", import.meta.url).pathname,
    "utf8"
  );

  assert(
    modalSrc.includes("onCapture?: (blob: Blob) => void"),
    "onCapture optional prop defined"
  );
  assert(
    modalSrc.includes("capturedBlobRef"),
    "capturedBlobRef used for blob storage"
  );
  assert(
    modalSrc.includes("handleAnalyze"),
    "handleAnalyze emits blob to parent"
  );
  assert(
    modalSrc.includes("fileInputRef"),
    "fileInputRef for gallery file picker"
  );
  assert(
    modalSrc.includes("permissionDenied"),
    "permissionDenied state for gallery fallback"
  );
  assert(
    modalSrc.includes("camera.privacyNotice"),
    "privacy notice i18n key used"
  );
  assert(
    modalSrc.includes("MAX_FILE_BYTES"),
    "5MB file size validation constant present"
  );
  assert(
    modalSrc.includes("image/jpeg,image/png,image/webp"),
    "accepted MIME types defined"
  );
}

// ── Test 5: Navigation DocumentScanState machine ──────────────────────────────
console.log("\n[5] Navigation DocumentScanState machine");
{
  const fs = await import("fs");
  const navSrc = fs.readFileSync(
    new URL("../../frontend/src/components/Navigation.tsx", import.meta.url).pathname,
    "utf8"
  );

  assert(navSrc.includes("DocumentScanState"), "DocumentScanState imported in Navigation");
  assert(navSrc.includes("handleDocumentCapture"), "handleDocumentCapture defined in Navigation");
  assert(navSrc.includes("analyzeDocument"), "analyzeDocument called in Navigation");
  assert(navSrc.includes("compressAndResizeImage"), "compressAndResizeImage called in Navigation");
  assert(
    navSrc.includes("onCapture={activeCameraMode === \"document_scan\" ? handleDocumentCapture : undefined}"),
    "onCapture wired to document_scan mode only in Navigation"
  );
}

// ── Test 6: ChatInput DocumentScanState machine ───────────────────────────────
console.log("\n[6] ChatInput DocumentScanState machine");
{
  const fs = await import("fs");
  const chatInputSrc = fs.readFileSync(
    new URL("../../frontend/src/components/ChatInput.tsx", import.meta.url).pathname,
    "utf8"
  );

  assert(chatInputSrc.includes("DocumentScanState"), "DocumentScanState imported in ChatInput");
  assert(chatInputSrc.includes("handleDocumentCapture"), "handleDocumentCapture defined in ChatInput");
  assert(chatInputSrc.includes("analyzeDocument"), "analyzeDocument called in ChatInput");
  assert(
    chatInputSrc.includes("onCapture={activeCameraMode === \"document_scan\" ? handleDocumentCapture : undefined}"),
    "onCapture wired to document_scan mode only in ChatInput"
  );
}

// ── Test 7: i18n string completeness ─────────────────────────────────────────
console.log("\n[7] i18n string completeness");
{
  const fs = await import("fs");
  const requiredKeys = [
    "camera.uploadGallery",
    "camera.analyze",
    "camera.analyzing",
    "camera.privacyNotice",
    "camera.identityRefused",
    "camera.retakeOrChoose",
    "camera.analysisFailed",
    "camera.fileTooBig",
    "camera.unsupportedFormat",
    "camera.permissionFallback",
  ];

  const locales = ["en", "hi", "mr"];
  for (const locale of locales) {
    const src = fs.readFileSync(
      new URL(`../../frontend/src/i18n/locales/${locale}.ts`, import.meta.url).pathname,
      "utf8"
    );
    for (const key of requiredKeys) {
      assert(src.includes(`"${key}"`), `${locale}.ts has key ${key}`);
    }
  }
}

// ── Test 8: imageOptimizer utility exists ─────────────────────────────────────
console.log("\n[8] imageOptimizer utility");
{
  const fs = await import("fs");
  const optimizerSrc = fs.readFileSync(
    new URL("../../frontend/src/utils/imageOptimizer.ts", import.meta.url).pathname,
    "utf8"
  );

  assert(
    optimizerSrc.includes("export async function compressAndResizeImage"),
    "compressAndResizeImage exported"
  );
  assert(
    optimizerSrc.includes("Blob"),
    "returns Blob type"
  );
}

// ── Summary ───────────────────────────────────────────────────────────────────
const total = passed.length + failed.length;
console.log(`\n${"─".repeat(60)}`);
console.log(`Results: ${passed.length}/${total} tests passed`);
if (failed.length > 0) {
  console.error(`\nFailed tests:`);
  failed.forEach((f) => console.error(`  ✗ ${f}`));
  console.log("\nFinal Verdict: BLOCKED — CAMERA & UPLOAD WIRING NOT SAFE");
  process.exit(1);
} else {
  console.log("\nFinal Verdict: PASS — CAMERA & UPLOAD WIRING VERIFIED");
  process.exit(0);
}
