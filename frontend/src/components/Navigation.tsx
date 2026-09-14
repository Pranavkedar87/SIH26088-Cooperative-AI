import React, { useState, useEffect, useCallback } from "react";
import type { AppTab, LanguageCode, DocumentScanState, VisionAnalyzeResponse } from "../types";
import { useTranslation } from "../i18n";
import {
  HomeIcon,
  MessageSquareIcon,
  MicIcon,
  CameraIcon,
  ClipboardCheckIcon,
  ScanDocIcon,
  FaceScanIcon,
} from "./Icons";
import { CameraCaptureModal, type CameraMode } from "./CameraCaptureModal";
import { analyzeDocument } from "../api/client";
import { compressAndResizeImage, MAX_UPLOAD_BYTES } from "../utils/imageOptimizer";

interface Props {
  activeTab: AppTab;
  onTabChange: (tab: AppTab) => void;
  language: LanguageCode;
  onOpenVoiceMode: () => void;
}

const Navigation: React.FC<Props> = ({
  activeTab,
  onTabChange,
  language,
  onOpenVoiceMode,
}) => {
  const [isCameraMenuOpen, setIsCameraMenuOpen] = useState(false);
  const [activeCameraMode, setActiveCameraMode] = useState<CameraMode | null>(null);
  const t = useTranslation(language);

  // Phase 3C.2 — DocumentScanState machine (Navigation copy)
  const [scanState, setScanState] = useState<DocumentScanState>("READY");
  const [_scanResult, setScanResult] = useState<VisionAnalyzeResponse | null>(null);
  const [_scanError, setScanError] = useState<string | null>(null);
  // Phase 3C.3 — granular progress step for UX ("compressing" | "analyzing" | null)
  const [scanProcessingStep, setScanProcessingStep] = useState<"compressing" | "analyzing" | null>(null);

  // Close camera popover on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isCameraMenuOpen) {
        setIsCameraMenuOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isCameraMenuOpen]);

  const handleSelectCameraMode = (mode: CameraMode) => {
    setIsCameraMenuOpen(false);
    setActiveCameraMode(mode);
  };

  /**
   * Phase 3C.2/3C.3 — Blob received from CameraCaptureModal (document_scan only).
   * Parent owns the full pipeline:
   *   Blob → compress (Phase 3C.3: size guard) → analyzeDocument → state update
   */
  const handleDocumentCapture = useCallback(
    async (blob: Blob) => {
      if (scanState === "ANALYZING") return; // prevent double-submission
      setScanState("ANALYZING");
      setScanError(null);
      setScanResult(null);

      try {
        // Phase 3C.3 — Step 1: compress & resize (show "Preparing image…")
        setScanProcessingStep("compressing");
        const compressed = await compressAndResizeImage(blob);

        // Phase 3C.3 — Size guard: reject before network call
        if (compressed.size > MAX_UPLOAD_BYTES) {
          setScanError(t("camera.optimizedTooLarge"));
          setScanState("ERROR");
          setScanProcessingStep(null);
          return;
        }

        // Phase 3C.3 — Step 2: analyze (show "Analyzing document…")
        setScanProcessingStep("analyzing");
        const result = await analyzeDocument(compressed, language);
        setScanResult(result);
        setScanState("RESULT");
        setScanProcessingStep(null);
        console.info("[VISION] Analysis complete:", result.document_type, result.readability);
      } catch (err: any) {
        console.error("[VISION] Nav analysis error:", err);
        setScanError(err?.message || t("camera.analysisFailed"));
        setScanState("ERROR");
        setScanProcessingStep(null);
      }
    },
    [scanState, language, t]
  );

  const voiceText = t("nav.voice");
  const cameraText = t("nav.camera");

  // Phase 3C.3 — progress label derived from scanProcessingStep
  const scanProgressLabel =
    scanProcessingStep === "compressing"
      ? t("camera.preparingImage")
      : scanProcessingStep === "analyzing"
      ? t("camera.analyzing")
      : null;

  return (
    <>
      <nav className="app-nav" aria-label="Primary Navigation">
        {/* Phase 3C.3 — document scan progress toast */}
        {scanProgressLabel && (
          <div className="vision-scan-toast" role="status" aria-live="polite">
            <span className="vision-scan-spinner" aria-hidden="true">⏳</span>
            <span>{scanProgressLabel}</span>
          </div>
        )}
        {/* Floating popover menu directly above the Camera button */}
        {isCameraMenuOpen && (
          <>
            <div
              className="nav-camera-popover-overlay"
              onClick={() => setIsCameraMenuOpen(false)}
              aria-hidden="true"
            />
            <div
              className="nav-camera-popover"
              role="menu"
              aria-label="Camera Options"
            >
              <button
                type="button"
                className="nav-camera-popover-item"
                onClick={() => handleSelectCameraMode("document_scan")}
                role="menuitem"
              >
                <div className="nav-camera-popover-icon-box">
                  <ScanDocIcon size={18} color="#0F6B68" />
                </div>
                <div className="nav-camera-popover-text">
                  <span className="nav-camera-popover-title">{t("nav.scanDocument")}</span>
                  <span className="nav-camera-popover-desc">{t("nav.scanDesc")}</span>
                </div>
              </button>

              <div className="nav-camera-popover-divider" />

              <button
                type="button"
                className="nav-camera-popover-item"
                onClick={() => handleSelectCameraMode("face_scan")}
                role="menuitem"
              >
                <div className="nav-camera-popover-icon-box">
                  <FaceScanIcon size={18} color="#0F6B68" />
                </div>
                <div className="nav-camera-popover-text">
                  <span className="nav-camera-popover-title">{t("nav.faceScan")}</span>
                  <span className="nav-camera-popover-desc">{t("nav.faceScanDesc")}</span>
                </div>
              </button>
            </div>
          </>
        )}

        <div className="nav-container">
          {/* 1. Home */}
          <button
            type="button"
            className={`nav-item ${activeTab === "home" ? "nav-item--active" : ""}`}
            onClick={() => onTabChange("home")}
            aria-selected={activeTab === "home"}
            role="tab"
          >
            <div className="nav-item__icon-wrapper">
              <HomeIcon size={20} color={activeTab === "home" ? "#123B5D" : "#68757D"} />
            </div>
            <span className="nav-item__label">{t("nav.home")}</span>
          </button>

          {/* 2. Ask AI */}
          <button
            type="button"
            className={`nav-item ${activeTab === "ask" ? "nav-item--active" : ""}`}
            onClick={() => onTabChange("ask")}
            aria-selected={activeTab === "ask"}
            role="tab"
          >
            <div className="nav-item__icon-wrapper">
              <MessageSquareIcon size={20} color={activeTab === "ask" ? "#123B5D" : "#68757D"} />
            </div>
            <span className="nav-item__label">{t("nav.askAI")}</span>
          </button>

          {/* 3. CENTER: Floating Highlighted Navy Blue Voice Action */}
          <div className="nav-center-voice-group">
            <button
              type="button"
              className="nav-floating-mic-btn"
              onClick={onOpenVoiceMode}
              aria-label={voiceText}
              title="Speak to SahkaarSetu"
            >
              <MicIcon size={26} color="#FFFFFF" />
            </button>
            <span className="nav-floating-btn-label nav-floating-btn-label--mic">
              {voiceText}
            </span>
          </div>

          {/* 4. CAMERA BUTTON */}
          <button
            type="button"
            className={`nav-item nav-camera-item ${isCameraMenuOpen ? "nav-item--active" : ""}`}
            onClick={() => setIsCameraMenuOpen((prev) => !prev)}
            aria-label={cameraText}
            title="Scan Document or Face"
          >
            <div className="nav-item__icon-wrapper">
              <CameraIcon size={20} color={isCameraMenuOpen ? "#123B5D" : "#0F6B68"} />
            </div>
            <span className="nav-item__label">{cameraText}</span>
          </button>

          {/* 5. Grievance */}
          <button
            type="button"
            className={`nav-item ${activeTab === "grievance" ? "nav-item--active" : ""}`}
            onClick={() => onTabChange("grievance")}
            aria-selected={activeTab === "grievance"}
            role="tab"
          >
            <div className="nav-item__icon-wrapper">
              <ClipboardCheckIcon size={20} color={activeTab === "grievance" ? "#123B5D" : "#68757D"} />
            </div>
            <span className="nav-item__label">{t("nav.grievance")}</span>
          </button>
        </div>
      </nav>

      {/* Camera Capture Modal */}
      {activeCameraMode && (
        <CameraCaptureModal
          mode={activeCameraMode}
          isOpen={Boolean(activeCameraMode)}
          onClose={() => setActiveCameraMode(null)}
          language={language}
          onCapture={activeCameraMode === "document_scan" ? handleDocumentCapture : undefined}
        />
      )}
    </>
  );
};

export default Navigation;
