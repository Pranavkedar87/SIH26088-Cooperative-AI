import React, { useState, useEffect } from "react";
import type { AppTab, LanguageCode } from "../types";
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

interface Props {
  activeTab: AppTab;
  onTabChange: (tab: AppTab) => void;
  language: LanguageCode;
  onOpenVoiceMode: () => void;
}

const VOICE_LABEL: Record<string, string> = {
  en: "Ask by Voice",
  hi: "बोलकर पूछें",
  mr: "बोलून विचारा",
  gu: "બોલીને પૂછો",
  ta: "குரல் மூலம்",
  bn: "ভয়েস দিয়ে",
};

const CAMERA_LABEL: Record<string, string> = {
  en: "Camera",
  hi: "कैमरा",
  mr: "कॅमेरा",
  gu: "કેમેરો",
  ta: "கேமரா",
  bn: "ক্যামেরা",
};

const Navigation: React.FC<Props> = ({
  activeTab,
  onTabChange,
  language,
  onOpenVoiceMode,
}) => {
  const [isCameraMenuOpen, setIsCameraMenuOpen] = useState(false);
  const [activeCameraMode, setActiveCameraMode] = useState<CameraMode | null>(null);

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

  const voiceText = VOICE_LABEL[language] ?? VOICE_LABEL.en;
  const cameraText = CAMERA_LABEL[language] ?? CAMERA_LABEL.en;

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
                  <span className="nav-camera-popover-title">Scan Document</span>
                  <span className="nav-camera-popover-desc">
                    Capture forms, receipts & certificates
                  </span>
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
                  <span className="nav-camera-popover-title">Face Scan (Optional)</span>
                  <span className="nav-camera-popover-desc">
                    Assistant preview feature
                  </span>
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
            <span className="nav-item__label">
              {language === "hi" ? "गृह" : language === "mr" ? "मुख्य" : "Home"}
            </span>
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
            <span className="nav-item__label">
              {language === "hi" ? "प्रश्न पूछें" : language === "mr" ? "प्रश्न विचारा" : "Ask AI"}
            </span>
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

          {/* 4. CAMERA BUTTON (Replaced Services) */}
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
            <span className="nav-item__label">
              {language === "hi" ? "शिकायत" : language === "mr" ? "तक्रार" : "Grievance"}
            </span>
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
        />
      )}
    </>
  );
};

export default Navigation;
