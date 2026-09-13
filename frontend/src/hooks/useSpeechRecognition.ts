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
  audioLevel?: number;
}

// Localized error messages for speech recognition
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

const RECORDING_TOO_SHORT_ERRORS: Record<string, string> = {
  hi: "रिकॉर्डिंग बहुत छोटी थी। कृपया पूरा वाक्य बोलें।",
  mr: "रेकॉर्डिंग खूप लहान होती. कृपया पूर्ण वाक्य बोला.",
  en: "Recording was too short. Please speak a full sentence.",
};

// VAD (Voice Activity Detection) Parameters
export const VAD_RMS_THRESHOLD = 0.015;      // RMS energy threshold above which speech is detected
export const VAD_MIN_SPEECH_TIME_MS = 1000;  // Minimum recording duration (1.0s) before silence detection can trigger
export const VAD_SILENCE_DURATION_MS = 1400; // 1.4s of sustained silence after speech detected triggers auto-stop
export const VAD_MAX_RECORDING_MS = 15000;   // 15.0s maximum safety cap to prevent runaway recording

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
  const [audioLevel, setAudioLevel] = useState<number>(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const vadRafIdRef = useRef<number | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const startTimeRef = useRef<number>(0);
  const hasSpokenRef = useRef<boolean>(false);
  const silenceStartRef = useRef<number | null>(null);
  const maxTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isStoppingRef = useRef<boolean>(false);

  const onTranscriptRef = useRef(onTranscript);
  useEffect(() => {
    onTranscriptRef.current = onTranscript;
  }, [onTranscript]);

  const isSupported =
    typeof window !== "undefined" &&
    Boolean(
      typeof navigator !== "undefined" &&
        navigator.mediaDevices &&
        typeof navigator.mediaDevices.getUserMedia === "function" &&
        typeof MediaRecorder !== "undefined"
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
    if (vadRafIdRef.current) {
      cancelAnimationFrame(vadRafIdRef.current);
      vadRafIdRef.current = null;
    }
    if (audioContextRef.current) {
      try {
        if (audioContextRef.current.state !== "closed") {
          audioContextRef.current.close();
        }
      } catch (e) {
        // Ignore close errors
      }
      audioContextRef.current = null;
    }
    analyserRef.current = null;

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
    hasSpokenRef.current = false;
    silenceStartRef.current = null;
    isStoppingRef.current = false;
    setAudioLevel(0);
  }, []);

  const stopListening = useCallback(() => {
    console.info("[VOICE] RECORDING_STOPPED requested");
    if (vadRafIdRef.current) {
      cancelAnimationFrame(vadRafIdRef.current);
      vadRafIdRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      try {
        isStoppingRef.current = true;
        mediaRecorderRef.current.stop();
      } catch (e) {
        console.warn("Error stopping MediaRecorder:", e);
        cleanupAudioResources();
        setStatus("idle");
      }
    } else {
      cleanupAudioResources();
      setStatus("idle");
    }
  }, [cleanupAudioResources]);

  const processAudioRecording = useCallback(
    async (chunks: Blob[], mimeType: string) => {
      setStatus("processing");
      console.info("[VOICE] RECORDING_STOPPED complete | chunks count:", chunks.length);

      const durationMs = Date.now() - startTimeRef.current;
      const audioBlob = new Blob(chunks, { type: mimeType || "audio/webm" });
      console.info("[VOICE] AUDIO_BLOB_CREATED");
      console.info("[VOICE] AUDIO_SIZE:", audioBlob.size, "bytes");
      console.info("[VOICE] AUDIO_MIME_TYPE:", audioBlob.type);
      console.info("[VOICE] RECORDING_DURATION:", durationMs, "ms | speech_detected:", hasSpokenRef.current);

      // Check for empty audio blob (< 100 bytes) or no speech activity detected
      if (audioBlob.size < 100) {
        console.warn("[VOICE] Recording empty:", audioBlob.size, "bytes");
        setStatus("error");
        setErrorMessage(NO_SPEECH_ERRORS[language] || NO_SPEECH_ERRORS["en"]);
        cleanupAudioResources();
        return;
      }

      // Check if user spoke for less than 400ms without meaningful speech
      if (durationMs < 400 && !hasSpokenRef.current) {
        console.warn("[VOICE] Recording too short (<400ms)");
        setStatus("error");
        setErrorMessage(RECORDING_TOO_SHORT_ERRORS[language] || RECORDING_TOO_SHORT_ERRORS["en"]);
        cleanupAudioResources();
        return;
      }

      try {
        console.info(`[STT] STT_REQUEST_STARTED provider=groq_whisper lang=${language} size=${audioBlob.size}`);
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
      console.info("[VOICE] Requesting microphone access (mono audio, noise suppression)...");
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      console.info("[VOICE] MIC_PERMISSION granted");
      mediaStreamRef.current = stream;

      // Initialize Web Audio API AnalyserNode for real-time RMS Voice Activity Detection (VAD)
      try {
        const AudioContextClass =
          window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        if (AudioContextClass) {
          const audioCtx = new AudioContextClass();
          const analyser = audioCtx.createAnalyser();
          analyser.fftSize = 512;
          const source = audioCtx.createMediaStreamSource(stream);
          source.connect(analyser);

          audioContextRef.current = audioCtx;
          analyserRef.current = analyser;
        }
      } catch (audioCtxErr) {
        console.warn("[VOICE] Web Audio API context initialization warning:", audioCtxErr);
      }

      const mimeType = getBestSupportedMimeType();
      const recorderOptions = mimeType ? { mimeType } : undefined;
      const mediaRecorder = new MediaRecorder(stream, recorderOptions);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      hasSpokenRef.current = false;
      silenceStartRef.current = null;
      startTimeRef.current = Date.now();

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

      // Start recording with 250ms chunk time slices
      mediaRecorder.start(250);
      setStatus("listening");
      console.info("[VOICE] RECORDING_STARTED mime=" + (mediaRecorder.mimeType || mimeType));

      // Start Real-Time RMS Silence Detection Loop (VAD)
      if (analyserRef.current) {
        const analyser = analyserRef.current;
        const buffer = new Float32Array(analyser.fftSize);

        const checkVAD = () => {
          if (!mediaRecorderRef.current || mediaRecorderRef.current.state !== "recording") {
            return;
          }

          analyser.getFloatTimeDomainData(buffer);
          let sumSquares = 0;
          for (let i = 0; i < buffer.length; i++) {
            sumSquares += buffer[i] * buffer[i];
          }
          const rms = Math.sqrt(sumSquares / buffer.length);
          setAudioLevel(Math.min(1, rms * 6));

          const now = Date.now();
          const recordingDuration = now - startTimeRef.current;

          if (rms > VAD_RMS_THRESHOLD) {
            // User is actively speaking
            hasSpokenRef.current = true;
            silenceStartRef.current = null;
          } else if (hasSpokenRef.current && recordingDuration >= VAD_MIN_SPEECH_TIME_MS) {
            // Speech was previously detected and min speech time has elapsed; track silence
            if (silenceStartRef.current === null) {
              silenceStartRef.current = now;
            } else if (now - silenceStartRef.current >= VAD_SILENCE_DURATION_MS) {
              console.info(
                `[VOICE] VAD: Sustained silence (${VAD_SILENCE_DURATION_MS}ms) detected after speech. Auto-stopping.`
              );
              stopListening();
              return;
            }
          }

          vadRafIdRef.current = requestAnimationFrame(checkVAD);
        };

        vadRafIdRef.current = requestAnimationFrame(checkVAD);
      }

      // Maximum Listening Timeout Safety Cap (Auto-stop after 15 seconds)
      maxTimerRef.current = setTimeout(() => {
        console.info(`[VOICE] Maximum recording safety timeout (${VAD_MAX_RECORDING_MS}ms) reached -> auto-stopping`);
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
          try {
            stopListening();
          } catch (e) {
            console.warn("Error auto-stopping recorder:", e);
          }
        }
      }, VAD_MAX_RECORDING_MS);

    } catch (err: any) {
      console.error("Microphone access error:", err);
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        console.info("[VOICE] MIC_PERMISSION denied");
        setStatus("error");
        setErrorMessage(PERMISSION_ERRORS[language] || PERMISSION_ERRORS["en"]);
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        console.info("[VOICE] No microphone device found");
        setStatus("error");
        setErrorMessage("Microphone not found. Please connect a microphone.");
      } else {
        setStatus("error");
        setErrorMessage(NO_SPEECH_ERRORS[language] || NO_SPEECH_ERRORS["en"]);
      }
      cleanupAudioResources();
    }
  }, [isSupported, language, processAudioRecording, stopListening, cleanupAudioResources]);

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
    audioLevel,
  };
}
