import { useState, useCallback, useRef, useEffect } from "react";
import type { LanguageCode, STTStatus } from "../types";
import { transcribeAudio } from "../api/client";

interface UseSpeechRecognitionOptions {
  language: LanguageCode;
  onTranscript: (text: string) => void;
  sessionId?: string;
}

interface UseSpeechRecognitionReturn {
  status: STTStatus;
  errorMessage: string | null;
  startListening: () => void;
  stopListening: () => void;
  clearError: () => void;
  isSupported: boolean;
}

declare global {
  interface Window {
    SpeechRecognition?: any;
    webkitSpeechRecognition?: any;
  }
}

const NO_SPEECH_ERRORS: Record<string, string> = {
  hi: "आवाज़ सुनाई नहीं दी। कृपया फिर से बोलें।",
  mr: "आवाज ऐकू आली नाही. कृपया पुन्हा बोला.",
  en: "I couldn't hear you. Please try again.",
};

const PERMISSION_ERRORS: Record<string, string> = {
  hi: "माइक्रोफ़ोन अनुमति अस्वीकृत। कृपया अनुमतियाँ जाँचें।",
  mr: "मायक्रोफोन परवानगी नाकारली. कृपया ब्राउझर सेटिंग तपासा.",
  en: "Microphone permission denied. Please check browser settings.",
};

function getBestSupportedMimeType(): string {
  if (typeof MediaRecorder === "undefined") return "";
  const candidateTypes = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/aac",
    "audio/ogg;codecs=opus",
    "audio/wav",
  ];
  for (const mime of candidateTypes) {
    if (MediaRecorder.isTypeSupported(mime)) {
      return mime;
    }
  }
  return "";
}

export function useSpeechRecognition({
  language,
  onTranscript,
  sessionId,
}: UseSpeechRecognitionOptions): UseSpeechRecognitionReturn {
  const [status, setStatus] = useState<STTStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const maxTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isStoppingRef = useRef<boolean>(false);

  const onTranscriptRef = useRef(onTranscript);
  useEffect(() => {
    onTranscriptRef.current = onTranscript;
  }, [onTranscript]);

  const isSupported = typeof window !== "undefined" && Boolean(
    (typeof navigator !== "undefined" && navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === "function" && typeof MediaRecorder !== "undefined") ||
    window.SpeechRecognition ||
    window.webkitSpeechRecognition
  );

  const clearError = useCallback(() => {
    setErrorMessage(null);
    setStatus("idle");
  }, []);

  const cleanupAudioResources = useCallback(() => {
    if (maxTimerRef.current) {
      clearTimeout(maxTimerRef.current);
      maxTimerRef.current = null;
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
    isStoppingRef.current = false;
  }, []);

  const stopListening = useCallback(() => {
    console.info("[VOICE] RECORDING_STOPPED requested");
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      try {
        isStoppingRef.current = true;
        mediaRecorderRef.current.stop();
      } catch (e) {
        console.warn("Error stopping MediaRecorder:", e);
      }
    } else {
      cleanupAudioResources();
      setStatus("idle");
    }
  }, [cleanupAudioResources]);

  const processAudioRecording = useCallback(
    async (chunks: Blob[], mimeType: string) => {
      setStatus("processing");
      console.info("[VOICE] RECORDING_STOPPED complete");

      const audioBlob = new Blob(chunks, { type: mimeType || "audio/webm" });
      console.info("[VOICE] AUDIO_BLOB_CREATED");
      console.info("[VOICE] AUDIO_SIZE:", audioBlob.size);
      console.info("[VOICE] AUDIO_MIME_TYPE:", audioBlob.type);

      // Check for empty or tiny recording (< 1.5 KB audio data)
      if (audioBlob.size < 1500) {
        console.warn("[VOICE] Recording too short or empty:", audioBlob.size, "bytes");
        setStatus("error");
        setErrorMessage(NO_SPEECH_ERRORS[language] || NO_SPEECH_ERRORS["en"]);
        cleanupAudioResources();
        return;
      }

      try {
        console.info("[STT] STT_REQUEST_STARTED provider=groq_whisper lang=" + language);
        const sttResult = await transcribeAudio(audioBlob, language, sessionId);

        const transcriptText = sttResult.transcript ? sttResult.transcript.trim() : "";
        console.info("[STT] STT_RESPONSE_RECEIVED");
        console.info("[STT] TRANSCRIPT_RECEIVED:", transcriptText);
        console.info("[STT] TRANSCRIPT_LENGTH:", transcriptText.length);
        console.info("[VOICE] DETECTED_LANGUAGE:", sttResult.language || language);

        if (!transcriptText) {
          setStatus("error");
          setErrorMessage(NO_SPEECH_ERRORS[language] || NO_SPEECH_ERRORS["en"]);
        } else {
          onTranscriptRef.current(transcriptText);
          setStatus("idle");
        }
      } catch (err: any) {
        console.error("[STT] Server STT failed:", err);
        setStatus("error");
        setErrorMessage(NO_SPEECH_ERRORS[language] || NO_SPEECH_ERRORS["en"]);
      } finally {
        cleanupAudioResources();
      }
    },
    [language, sessionId, cleanupAudioResources]
  );

  const startListening = useCallback(async () => {
    setErrorMessage(null);
    cleanupAudioResources();

    if (!isSupported) {
      setStatus("unsupported");
      setErrorMessage("Voice input is not supported in this browser.");
      return;
    }

    try {
      console.info("[VOICE] Requesting microphone permission...");
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      console.info("[VOICE] MIC_PERMISSION granted");
      mediaStreamRef.current = stream;

      const mimeType = getBestSupportedMimeType();
      const recorderOptions = mimeType ? { mimeType } : undefined;
      const mediaRecorder = new MediaRecorder(stream, recorderOptions);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const capturedChunks = [...audioChunksRef.current];
        processAudioRecording(capturedChunks, mediaRecorder.mimeType || mimeType);
      };

      mediaRecorder.onerror = (event: any) => {
        console.error("MediaRecorder error:", event);
        setStatus("error");
        setErrorMessage(NO_SPEECH_ERRORS[language] || NO_SPEECH_ERRORS["en"]);
        cleanupAudioResources();
      };

      // Start recording with 250ms time slices
      mediaRecorder.start(250);
      setStatus("listening");
      console.info("[VOICE] RECORDING_STARTED mime=" + (mediaRecorder.mimeType || mimeType));

      // Maximum Listening Timeout (Auto-stop after 8.5 seconds)
      maxTimerRef.current = setTimeout(() => {
        console.info("[VOICE] Listening timeout reached (8.5s) -> auto-stopping recording");
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
          try {
            mediaRecorderRef.current.stop();
          } catch (e) {
            console.warn("Error auto-stopping recorder:", e);
          }
        }
      }, 8500);

    } catch (err: any) {
      console.error("Microphone access error:", err);
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        console.info("[VOICE] MIC_PERMISSION denied");
        setStatus("error");
        setErrorMessage(PERMISSION_ERRORS[language] || PERMISSION_ERRORS["en"]);
      } else {
        setStatus("error");
        setErrorMessage(NO_SPEECH_ERRORS[language] || NO_SPEECH_ERRORS["en"]);
      }
      cleanupAudioResources();
    }
  }, [isSupported, language, processAudioRecording, cleanupAudioResources]);

  // Clean up on unmount or language change
  useEffect(() => {
    return () => {
      cleanupAudioResources();
    };
  }, [language, cleanupAudioResources]);

  return {
    status,
    errorMessage,
    startListening,
    stopListening,
    clearError,
    isSupported,
  };
}
