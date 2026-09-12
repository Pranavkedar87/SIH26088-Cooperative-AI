import React, { useState, useEffect, useRef, useCallback } from "react";
import type { LanguageCode } from "../types";
import { useTranslation } from "../i18n";
import {
  ScanDocIcon,
  FaceScanIcon,
  XIcon,
  FlipCameraIcon,
  RotateCcwIcon,
  CheckIcon,
  AlertTriangleIcon,
} from "./Icons";

export type CameraMode = "document_scan" | "face_scan";

interface CameraCaptureModalProps {
  mode: CameraMode;
  isOpen: boolean;
  onClose: () => void;
  language: LanguageCode;
}

const LABELS = {
  document_scan: {
    title: {
      en: "Scan Document",
      hi: "दस्तावेज़ स्कैन करें",
      mr: "कागदपत्र स्कॅन करा",
    },
    hint: {
      en: "Position your document inside the frame for clear visibility.",
      hi: "स्पष्टता के लिए अपने दस्तावेज़ को फ्रेम के अंदर रखें।",
      mr: "स्पष्टतेसाठी तुमचे कागदपत्र फ्रेमच्या आत ठेवा.",
    },
    disclaimer: {
      en: "Document capture is ready for future OCR & institutional processing.",
      hi: "दस्तावेज़ कैप्चर भविष्य के ओसीआर और संस्थागत उपयोग के लिए तैयार है।",
      mr: "कागदपत्र कॅप्चर भविष्यातील ओसीआर आणि संस्थागत प्रक्रियेसाठी सज्ज आहे.",
    },
    capturedMessage: {
      en: "Document image captured successfully. Document analysis interface extension point is active.",
      hi: "दस्तावेज़ छवि सफलतापूर्वक कैप्चर की गई।",
      mr: "कागदपत्र प्रतिमा यशस्वीपणे कॅप्चर झाली.",
    },
  },
  face_scan: {
    title: {
      en: "Face Scan (Optional)",
      hi: "फेस स्कैन (वैकल्पिक)",
      mr: "फेस स्कॅन (पर्यायी)",
    },
    hint: {
      en: "Align face inside the oval frame. Optional preview functionality.",
      hi: "अंडाकार फ्रेम के अंदर चेहरा रखें। वैकल्पिक पूर्वावलोकन।",
      mr: "अंडाकृती फ्रेममध्ये चेहरा ठेवा. पर्यायी पूर्वावलोकन.",
    },
    disclaimer: {
      en: "Notice: No biometric data or facial templates are stored, authenticated, or transmitted.",
      hi: "सूचना: कोई भी बायोमेट्रिक डेटा या चेहरा सहेजा या सत्यापित नहीं किया जाता है।",
      mr: "सूचना: कोणताही बायोमेट्रिक डेटा साठवला किंवा पडताळला जात नाही.",
    },
    capturedMessage: {
      en: "Face preview captured. No biometric matching or identity verification is performed.",
      hi: "फेस पूर्वावलोकन कैप्चर किया गया। कोई बायोमेट्रिक मिलान नहीं किया जाता।",
      mr: "फेस पूर्वावलोकन कॅप्चर झाले. कोणतीही बायोमेट्रिक पडताळणी केली जात नाही.",
    },
  },
};

export const CameraCaptureModal: React.FC<CameraCaptureModalProps> = ({
  mode,
  isOpen,
  onClose,
  language,
}) => {
  const t = useTranslation(language);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [cameraFacing, setCameraFacing] = useState<"user" | "environment">(
    mode === "document_scan" ? "environment" : "user"
  );
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Start live stream
  const startCamera = useCallback(async (facing: "user" | "environment") => {
    setErrorMsg(null);
    setCapturedImage(null);
    try {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Camera API is not supported by your browser environment.");
      }

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: facing,
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });

      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err: unknown) {
      console.warn("Camera access note:", err);
      const isDenied =
        err instanceof Error &&
        (err.name === "NotAllowedError" || err.name === "PermissionDeniedError");
      setErrorMsg(
        isDenied
          ? "Camera permission was denied. Please allow camera access in your browser settings to scan."
          : "Camera not available or not detected in this environment."
      );
    }
  }, [stream]);

  // Clean up streams
  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  }, [stream]);

  // Open / Close lifecycle
  useEffect(() => {
    if (isOpen) {
      const initialFacing = mode === "document_scan" ? "environment" : "user";
      setCameraFacing(initialFacing);
      startCamera(initialFacing);
    } else {
      stopCamera();
      setCapturedImage(null);
      setErrorMsg(null);
    }
    return () => {
      stopCamera();
    };
  }, [isOpen, mode]);

  // Flip camera toggle
  const handleFlipCamera = () => {
    const nextFacing = cameraFacing === "user" ? "environment" : "user";
    setCameraFacing(nextFacing);
    startCamera(nextFacing);
  };

  // Capture frame
  const handleCapture = () => {
    setIsCapturing(true);
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL("image/jpeg", 0.9);
        setCapturedImage(dataUrl);
      }
    } else {
      // Fallback placeholder preview if camera stream not rendered
      setCapturedImage(
        "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='300' fill='%23123B5D'><rect width='400' height='300' fill='%23EBF2F7'/><text x='50%25' y='50%25' text-anchor='middle' fill='%23123B5D' font-family='sans-serif' font-size='16'>Captured Preview</text></svg>"
      );
    }
    setIsCapturing(false);
  };

  const handleRetake = () => {
    setCapturedImage(null);
    startCamera(cameraFacing);
  };

  if (!isOpen) return null;

  const currentLabels = LABELS[mode];
  const langKey = language in currentLabels.title ? language : "en";

  return (
    <div className="camera-modal-backdrop" role="dialog" aria-modal="true">
      <div className="camera-modal-card">
        {/* Modal Header */}
        <div className="camera-modal-header">
          <div className="camera-modal-title-wrap">
            {mode === "document_scan" ? (
              <ScanDocIcon size={20} color="#0F6B68" />
            ) : (
              <FaceScanIcon size={20} color="#0F6B68" />
            )}
            <div>
              <h2 className="camera-modal-title">
                {currentLabels.title[langKey as keyof typeof currentLabels.title] || currentLabels.title.en}
              </h2>
              <span className="camera-modal-sub">
                {mode === "document_scan" ? t("camera.docAssist") : t("camera.optionalPreview")}
              </span>
            </div>
          </div>
          <button
            type="button"
            className="camera-close-btn"
            onClick={onClose}
            aria-label={t("common.close")}
          >
            <XIcon size={18} color="#24323A" />
          </button>
        </div>

        {/* Viewfinder / Capture Box */}
        <div className="camera-viewfinder-container">
          {!capturedImage ? (
            <>
              {errorMsg ? (
                <div className="camera-error-view">
                  <AlertTriangleIcon size={32} color="#F28C28" />
                  <p className="camera-error-text">{errorMsg}</p>
                  <button
                    type="button"
                    className="camera-action-btn camera-btn-primary"
                    onClick={() => startCamera(cameraFacing)}
                  >
                    {t("camera.retry")}
                  </button>
                </div>
              ) : (
                <div className="camera-video-wrapper">
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className={`camera-video-feed ${
                      cameraFacing === "user" ? "camera-video-mirrored" : ""
                    }`}
                  />
                  {/* Framing Overlay */}
                  {mode === "document_scan" ? (
                    <div className="camera-guide-document">
                      <div className="guide-corner top-left" />
                      <div className="guide-corner top-right" />
                      <div className="guide-corner bottom-left" />
                      <div className="guide-corner bottom-right" />
                      <div className="guide-scan-line" />
                    </div>
                  ) : (
                    <div className="camera-guide-face">
                      <div className="guide-face-oval" />
                    </div>
                  )}

                  {/* Top helper tag */}
                  <div className="camera-viewfinder-hint">
                    {currentLabels.hint[langKey as keyof typeof currentLabels.hint] || currentLabels.hint.en}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="camera-preview-wrapper">
              <img
                src={capturedImage}
                alt="Captured scan preview"
                className="camera-preview-img"
              />
              <div className="camera-preview-badge">
                <CheckIcon size={14} color="#0F6B68" />
                <span>{t("camera.captured")}</span>
              </div>
            </div>
          )}
        </div>

        {/* Hidden offscreen canvas for snapshot rendering */}
        <canvas ref={canvasRef} style={{ display: "none" }} />

        {/* Informative Disclaimer / Future Readiness Banner */}
        <div className="camera-disclaimer-banner">
          <p>
            {capturedImage
              ? (currentLabels.capturedMessage[
                  langKey as keyof typeof currentLabels.capturedMessage
                ] || currentLabels.capturedMessage.en)
              : (currentLabels.disclaimer[
                  langKey as keyof typeof currentLabels.disclaimer
                ] || currentLabels.disclaimer.en)}
          </p>
        </div>

        {/* Controls Footer */}
        <div className="camera-modal-footer">
          {!capturedImage ? (
            <div className="camera-controls-row">
              <button
                type="button"
                className="camera-tool-btn"
                onClick={handleFlipCamera}
                title={t("common.flip")}
                aria-label={t("common.flip")}
              >
                <FlipCameraIcon size={18} color="#123B5D" />
                <span>{t("common.flip")}</span>
              </button>

              <button
                type="button"
                className="camera-shutter-btn"
                onClick={handleCapture}
                disabled={isCapturing}
                aria-label="Capture photo"
              >
                <div className="shutter-inner" />
              </button>

              <button
                type="button"
                className="camera-tool-btn"
                onClick={onClose}
                aria-label={t("common.cancel")}
              >
                <span>{t("common.cancel")}</span>
              </button>
            </div>
          ) : (
            <div className="camera-captured-actions">
              <button
                type="button"
                className="camera-action-btn camera-btn-secondary"
                onClick={handleRetake}
              >
                <RotateCcwIcon size={16} color="#123B5D" />
                <span>{t("camera.retake")}</span>
              </button>
              <button
                type="button"
                className="camera-action-btn camera-btn-primary"
                onClick={onClose}
              >
                <CheckIcon size={16} color="#FFFFFF" />
                <span>{t("common.done")}</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
