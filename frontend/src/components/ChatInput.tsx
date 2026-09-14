import React, { useState, useRef, useCallback, useEffect } from "react";
import type { LanguageCode, DocumentScanState, VisionAnalyzeResponse } from "../types";
import { useTranslation } from "../i18n";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";
import { CameraIcon, MicIcon, SendIcon, ScanDocIcon, FaceScanIcon } from "./Icons";
import { CameraCaptureModal, type CameraMode } from "./CameraCaptureModal";
import { analyzeDocument } from "../api/client";
import { compressAndResizeImage, MAX_UPLOAD_BYTES } from "../utils/imageOptimizer";

interface Props {
  language: LanguageCode;
  isLoading: boolean;
  onSend: (message: string) => void;
  value: string;
  onChange: (value: string) => void;
}

const ChatInput: React.FC<Props> = ({ language, isLoading, onSend, value, onChange }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [activeCameraMode, setActiveCameraMode] = useState<CameraMode | null>(null);
  const t = useTranslation(language);

  // Phase 3C.2 — DocumentScanState machine (ChatInput copy)
  const [scanState, setScanState] = useState<DocumentScanState>("READY");
  const [_scanResult, setScanResult] = useState<VisionAnalyzeResponse | null>(null);
  const [_scanError, setScanError] = useState<string | null>(null);
  // Phase 3C.3 — granular progress step ("compressing" | "analyzing" | null)
  const [scanProcessingStep, setScanProcessingStep] = useState<"compressing" | "analyzing" | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  // Close popover on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isMenuOpen) {
        setIsMenuOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isMenuOpen]);

  const handleTranscript = useCallback(
    (text: string) => {
      const newText = value ? `${value} ${text}` : text;
      onChange(newText);
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
        textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
        textareaRef.current.focus();
      }
    },
    [value, onChange]
  );

  const { status, errorMessage, startListening, stopListening, clearError, isSupported } =
    useSpeechRecognition({
      language,
      onTranscript: handleTranscript,
    });

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    if (status === "listening") {
      stopListening();
    }
    clearError();
    onSend(trimmed);
    onChange("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.focus();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (errorMessage) {
      clearError();
    }
    onChange(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
    }
  };

  const handleMicClick = () => {
    if (isMenuOpen) setIsMenuOpen(false);
    if (status === "listening") {
      stopListening();
    } else {
      clearError();
      startListening();
    }
  };

  const toggleCameraMenu = () => {
    setIsMenuOpen((prev) => !prev);
  };

  const handleSelectOption = (mode: CameraMode) => {
    setIsMenuOpen(false);
    setActiveCameraMode(mode);
  };

  /**
   * Phase 3C.2/3C.3 — Blob received from CameraCaptureModal (document_scan only).
   * Parent owns the full pipeline:
   *   Blob → compress (Phase 3C.3: size guard) → analyzeDocument → state update
   */
  const handleDocumentCapture = useCallback(
    async (blob: Blob) => {
      if (scanState === "ANALYZING") return;
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
        console.info("[VISION] ChatInput analysis complete:", result.document_type, result.readability);
      } catch (err: any) {
        console.error("[VISION] ChatInput analysis error:", err);
        setScanError(err?.message || t("camera.analysisFailed"));
        setScanState("ERROR");
        setScanProcessingStep(null);
      }
    },
    [scanState, language, t]
  );

  // Phase 3C.3 — progress label derived from scanProcessingStep
  const scanProgressLabel =
    scanProcessingStep === "compressing"
      ? t("camera.preparingImage")
      : scanProcessingStep === "analyzing"
      ? t("camera.analyzing")
      : null;

  return (
    <div className="input-bar-container">
      {/* Phase 3C.3 — document scan progress badge */}
      {scanProgressLabel && (
        <div className="stt-status-bar stt-status-bar--processing vision-scan-progress" role="status" aria-live="polite">
          <span aria-hidden="true">⏳</span>
          <span>{scanProgressLabel}</span>
        </div>
      )}
      {/* Popover Action Menu */}
      {isMenuOpen && (
        <>
          <div
            className="camera-popover-overlay"
            onClick={() => setIsMenuOpen(false)}
            aria-hidden="true"
          />
          <div
            ref={popoverRef}
            className="camera-action-popover"
            role="menu"
            aria-label="Camera Actions"
          >
            <button
              type="button"
              className="camera-popover-item"
              onClick={() => handleSelectOption("document_scan")}
              role="menuitem"
            >
              <div className="camera-popover-icon-box">
                <ScanDocIcon size={18} color="#0F6B68" />
              </div>
              <div className="camera-popover-text">
                <span className="camera-popover-title">{t("nav.scanDocument")}</span>
                <span className="camera-popover-desc">{t("nav.scanDesc")}</span>
              </div>
            </button>

            <div className="camera-popover-divider" />

            <button
              type="button"
              className="camera-popover-item"
              onClick={() => handleSelectOption("face_scan")}
              role="menuitem"
            >
              <div className="camera-popover-icon-box">
                <FaceScanIcon size={18} color="#0F6B68" />
              </div>
              <div className="camera-popover-text">
                <span className="camera-popover-title">{t("nav.faceScan")}</span>
                <span className="camera-popover-desc">{t("nav.faceScanDesc")}</span>
              </div>
            </button>
          </div>
        </>
      )}

      {/* Listening or processing status badge */}
      {status === "listening" && (
        <div className="stt-status-bar stt-status-bar--listening" role="status" aria-live="polite">
          <MicIcon size={14} color="#B94A48" />
          <span>{t("input.sttListening")}</span>
        </div>
      )}
      {status === "processing" && (
        <div className="stt-status-bar stt-status-bar--processing" role="status" aria-live="polite">
          <span>{t("input.sttProcessing")}</span>
        </div>
      )}
      {errorMessage && status === "error" && (
        <div className="stt-status-bar stt-status-bar--error" role="alert">
          <span>{errorMessage}</span>
          <button
            type="button"
            className="stt-dismiss-btn"
            onClick={clearError}
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}

      <div className="input-sticky-bar">
        <textarea
          ref={textareaRef}
          className="input-textarea"
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={t("input.placeholder")}
          rows={1}
          disabled={isLoading}
          aria-label="Message input"
          maxLength={2000}
        />

        {/* Camera Button */}
        <button
          type="button"
          className={`input-btn camera-btn ${isMenuOpen ? "camera-btn--active" : ""}`}
          onClick={toggleCameraMenu}
          disabled={isLoading}
          aria-label="Camera options"
          title="Scan document or face"
        >
          <CameraIcon size={18} color="#0F6B68" />
        </button>

        {/* Microphone Button */}
        <button
          type="button"
          className={`input-btn mic-btn ${status === "listening" ? "mic-btn--active" : ""}`}
          onClick={handleMicClick}
          disabled={isLoading}
          aria-label={status === "listening" ? t("home.clickToStop") : t("home.clickToSpeak")}
          title={
            !isSupported
              ? t("home.voiceNotSupported")
              : status === "listening"
              ? t("home.clickToStop")
              : t("home.clickToSpeak")
          }
        >
          <MicIcon size={18} color={status === "listening" ? "#C53030" : "#0F6B68"} />
        </button>

        {/* Send Button */}
        <button
          type="button"
          className="input-btn send-btn"
          onClick={handleSend}
          disabled={!value.trim() || isLoading}
          aria-label={t("input.sendMessage")}
        >
          <SendIcon size={18} color="#FFFFFF" />
        </button>
      </div>

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
    </div>
  );
};

export default ChatInput;
