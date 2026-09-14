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
import { compressAndResizeImage } from "../utils/imageOptimizer";

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
   * Phase 3C.2 — Blob received from CameraCaptureModal (document_scan only).
   * Parent owns API call; modal is decoupled from network logic.
   */
  const handleDocumentCapture = useCallback(
    async (blob: Blob) => {
      if (scanState === "ANALYZING") return; // prevent double-submission
      setScanState("ANALYZING");
      setScanError(null);
      setScanResult(null);

      try {
        // Compress before upload
        const compressed = await compressAndResizeImage(blob);
        const result = await analyzeDocument(compressed, language);
        setScanResult(result);
        setScanState("RESULT");
        // Phase 3C.3 will consume result — extension point active
        console.info("[VISION] Analysis complete:", result.document_type, result.readability);
      } catch (err: any) {
        console.error("[VISION] Nav analysis error:", err);
        setScanError(err?.message || t("camera.analysisFailed"));
        setScanState("ERROR");
      }
    },
    [scanState, language, t]
  );

  const voiceText = t("nav.voice");
  const cameraText = t("nav.camera");

  return (
    <>
      <nav className="app-nav" aria-label="Primary Navigation">
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
