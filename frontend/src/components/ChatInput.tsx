import React, { useState, useRef, useCallback, useEffect } from "react";
import type { LanguageCode } from "../types";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";
import { CameraIcon, MicIcon, SendIcon, ScanDocIcon, FaceScanIcon } from "./Icons";
import { CameraCaptureModal, type CameraMode } from "./CameraCaptureModal";

interface Props {
  language: LanguageCode;
  isLoading: boolean;
  onSend: (message: string) => void;
  value: string;
  onChange: (value: string) => void;
}

const PLACEHOLDER: Record<string, string> = {
  en: "Ask me anything — schemes, science, history, or any topic…",
  hi: "कुछ भी पूछें — योजनाएं, विज्ञान, इतिहास, या कोई भी विषय…",
  mr: "काहीही विचारा — योजना, विज्ञान, इतिहास किंवा कोणताही विषय…",
};

const STT_STATUS_LABEL: Record<string, { listening: string; processing: string }> = {
  en: { listening: "Listening… Speak now", processing: "Processing speech…" },
  hi: { listening: "सुन रहा हूँ… अब बोलें", processing: "आवाज संसाधित हो रही है…" },
  mr: { listening: "ऐकत आहे… आता बोला", processing: "आवाज प्रक्रिया सुरू आहे…" },
};

const ChatInput: React.FC<Props> = ({ language, isLoading, onSend, value, onChange }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [activeCameraMode, setActiveCameraMode] = useState<CameraMode | null>(null);

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

  return (
    <div className="input-bar-container">
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
                <span className="camera-popover-title">Scan Document</span>
                <span className="camera-popover-desc">Capture records, forms, or certificates</span>
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
                <span className="camera-popover-title">Face Scan (Optional)</span>
                <span className="camera-popover-desc">Additional camera feature preview</span>
              </div>
            </button>
          </div>
        </>
      )}

      {/* Listening or processing status badge */}
      {status === "listening" && (
        <div className="stt-status-bar stt-status-bar--listening" role="status" aria-live="polite">
          <MicIcon size={14} color="#B94A48" />
          <span>{(STT_STATUS_LABEL[language] ?? STT_STATUS_LABEL.en).listening}</span>
        </div>
      )}
      {status === "processing" && (
        <div className="stt-status-bar stt-status-bar--processing" role="status" aria-live="polite">
          <span>{(STT_STATUS_LABEL[language] ?? STT_STATUS_LABEL.en).processing}</span>
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
          placeholder={PLACEHOLDER[language] ?? PLACEHOLDER.en}
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
          aria-label={status === "listening" ? "Stop voice input" : "Start voice input"}
          title={
            !isSupported
              ? "Voice input not supported"
              : status === "listening"
              ? "Listening… Click to stop"
              : "Click to speak"
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
          aria-label="Send message"
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
        />
      )}
    </div>
  );
};

export default ChatInput;
