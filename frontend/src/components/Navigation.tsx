import React, { useState, useEffect } from "react";
import type { AppTab, LanguageCode } from "../types";
import {
  HomeIcon,
  MessageSquareIcon,
  MicIcon,
  CameraIcon,
  GridIcon,
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

const TAB_CONFIG: Array<{
  id: AppTab;
  icon: React.FC<{ size?: number; color?: string }>;
  en: string;
  hi: string;
  mr: string;
}> = [
  { id: "home", icon: HomeIcon, en: "Home", hi: "गृह", mr: "मुख्य" },
  { id: "ask", icon: MessageSquareIcon, en: "Ask AI", hi: "प्रश्न पूछें", mr: "प्रश्न विचारा" },
  { id: "services", icon: GridIcon, en: "Services", hi: "सेवाएं", mr: "सेवा" },
  { id: "grievance", icon: ClipboardCheckIcon, en: "Grievance", hi: "शिकायत", mr: "तक्रार" },
];

const VOICE_LABEL: Record<string, string> = {
  en: "Ask by Voice",
  hi: "बोलकर पूछें",
  mr: "बोलून विचारा",
  gu: "બોલીને પૂછો",
  ta: "குரல் மூலம்",
  bn: "ভয়েস দিয়ে",
};

const SCAN_LABEL: Record<string, string> = {
  en: "Scan",
  hi: "स्कैन",
  mr: "स्कॅन",
  gu: "સ્કેન",
  ta: "ஸ்கேன்",
  bn: "স্ক্যান",
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
  const scanText = SCAN_LABEL[language] ?? SCAN_LABEL.en;

  return (
    <>
      <nav className="app-nav" aria-label="Primary Navigation">
        {/* Floating popover menu directly above the floating camera button */}
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
              aria-label="Scan Options"
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
          {/* Tab 1: Home */}
          {(() => {
            const tab = TAB_CONFIG[0];
            const IconComp = tab.icon;
            const label = (tab as any)[language] ?? tab.en;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                className={`nav-item ${isActive ? "nav-item--active" : ""}`}
                onClick={() => onTabChange(tab.id)}
                aria-selected={isActive}
                role="tab"
              >
                <div className="nav-item__icon-wrapper">
                  <IconComp size={20} color={isActive ? "#123B5D" : "#68757D"} />
                </div>
                <span className="nav-item__label">{label}</span>
              </button>
            );
          })()}

          {/* Tab 2: Ask AI */}
          {(() => {
            const tab = TAB_CONFIG[1];
            const IconComp = tab.icon;
            const label = (tab as any)[language] ?? tab.en;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                className={`nav-item ${isActive ? "nav-item--active" : ""}`}
                onClick={() => onTabChange(tab.id)}
                aria-selected={isActive}
                role="tab"
              >
                <div className="nav-item__icon-wrapper">
                  <IconComp size={20} color={isActive ? "#123B5D" : "#68757D"} />
                </div>
                <span className="nav-item__label">{label}</span>
              </button>
            );
          })()}

          {/* Center Floating Actions: Primary Navy Mic + Right Shifted Floating Camera */}
          <div className="nav-floating-center-dock">
            {/* 1. Primary Highlighted Navy Mic Button */}
            <div className="nav-floating-action-group">
              <button
                type="button"
                className="nav-floating-mic-btn"
                onClick={onOpenVoiceMode}
                aria-label={voiceText}
                title="Speak to SahkaarSetu"
              >
                <MicIcon size={24} color="#FFFFFF" />
              </button>
              <span className="nav-floating-btn-label nav-floating-btn-label--mic">
                {voiceText}
              </span>
            </div>

            {/* 2. Floating Camera Button shifted to the right of the mic */}
            <div className="nav-floating-action-group">
              <button
                type="button"
                className={`nav-floating-camera-btn ${
                  isCameraMenuOpen ? "nav-floating-camera-btn--active" : ""
                }`}
                onClick={() => setIsCameraMenuOpen((prev) => !prev)}
                aria-label={scanText}
                title="Scan Document or Face"
              >
                <CameraIcon size={18} color="#0F6B68" />
              </button>
              <span className="nav-floating-btn-label nav-floating-btn-label--camera">
                {scanText}
              </span>
            </div>
          </div>

          {/* Tab 3: Services */}
          {(() => {
            const tab = TAB_CONFIG[2];
            const IconComp = tab.icon;
            const label = (tab as any)[language] ?? tab.en;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                className={`nav-item ${isActive ? "nav-item--active" : ""}`}
                onClick={() => onTabChange(tab.id)}
                aria-selected={isActive}
                role="tab"
              >
                <div className="nav-item__icon-wrapper">
                  <IconComp size={20} color={isActive ? "#123B5D" : "#68757D"} />
                </div>
                <span className="nav-item__label">{label}</span>
              </button>
            );
          })()}

          {/* Tab 4: Grievance */}
          {(() => {
            const tab = TAB_CONFIG[3];
            const IconComp = tab.icon;
            const label = (tab as any)[language] ?? tab.en;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                className={`nav-item ${isActive ? "nav-item--active" : ""}`}
                onClick={() => onTabChange(tab.id)}
                aria-selected={isActive}
                role="tab"
              >
                <div className="nav-item__icon-wrapper">
                  <IconComp size={20} color={isActive ? "#123B5D" : "#68757D"} />
                </div>
                <span className="nav-item__label">{label}</span>
              </button>
            );
          })()}
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
