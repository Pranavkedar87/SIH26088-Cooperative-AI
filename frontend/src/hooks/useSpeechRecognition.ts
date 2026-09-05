import { useState, useCallback, useRef, useEffect } from "react";
import type { LanguageCode, STTStatus } from "../types";

const STT_LANG_MAP: Record<LanguageCode, string[]> = {
  en: ["en-IN", "en-US", "en"],
  hi: ["hi-IN", "hi"],
  mr: ["mr-IN", "mr", "hi-IN", "en-IN"], // Fallback languages if browser lacks Marathi STT pack
};

interface UseSpeechRecognitionOptions {
  language: LanguageCode;
  onTranscript: (text: string) => void;
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

export function useSpeechRecognition({
  language,
  onTranscript,
}: UseSpeechRecognitionOptions): UseSpeechRecognitionReturn {
  const [status, setStatus] = useState<STTStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);
  const langIndexRef = useRef<number>(0);

  const SpeechRecognitionClass =
    typeof window !== "undefined"
      ? window.SpeechRecognition || window.webkitSpeechRecognition
      : null;

  const isSupported = Boolean(SpeechRecognitionClass);

  const clearError = useCallback(() => {
    setErrorMessage(null);
    if (status === "error") {
      setStatus("idle");
    }
  }, [status]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // Ignore stop errors if already stopped
      }
      recognitionRef.current = null;
    }
    setStatus("idle");
  }, []);

  const startListening = useCallback(() => {
    setErrorMessage(null);

    if (!SpeechRecognitionClass) {
      setStatus("unsupported");
      setErrorMessage("Voice input is not supported in this browser. You can type your question instead.");
      return;
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (e) {
        // Ignore abort errors
      }
    }

    const targetLangs = STT_LANG_MAP[language] || ["en-IN"];
    const currentLang = targetLangs[langIndexRef.current % targetLangs.length];

    try {
      const recognition = new SpeechRecognitionClass();
      recognition.lang = currentLang;
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => {
        setStatus("listening");
      };

      recognition.onresult = (event: any) => {
        setStatus("processing");
        if (event.results && event.results[0] && event.results[0][0]) {
          const text = event.results[0][0].transcript;
          if (text && text.trim()) {
            onTranscript(text.trim());
          }
        }
        setStatus("idle");
      };

      recognition.onerror = (event: any) => {
        const err = event.error;
        console.warn("Speech recognition error:", err, "lang:", currentLang);

        if (err === "not-allowed" || err === "permission-denied") {
          setStatus("error");
          setErrorMessage("Microphone permission denied. Please allow microphone access in your browser settings.");
        } else if (err === "no-speech") {
          setStatus("error");
          setErrorMessage("No speech detected. Please try speaking again.");
        } else if (err === "service-not-allowed") {
          setStatus("error");
          setErrorMessage("Voice recognition service not enabled in browser. Please check microphone/Siri settings or try Google Chrome.");
        } else if (err === "language-not-supported") {
          // Retry with next fallback language code if available
          if (langIndexRef.current < targetLangs.length - 1) {
            langIndexRef.current += 1;
            console.info("Retrying STT with fallback language:", targetLangs[langIndexRef.current]);
            startListening();
            return;
          }
          setStatus("error");
          setErrorMessage("Selected language is not supported by your browser's speech engine. Try typing or use Google Chrome.");
        } else if (err === "audio-capture") {
          setStatus("error");
          setErrorMessage("No microphone detected. Please connect a microphone and try again.");
        } else {
          setStatus("error");
          setErrorMessage("Voice input unavailable in this browser session. You can type your question instead.");
        }
      };

      recognition.onend = () => {
        setStatus((prev) => (prev === "listening" || prev === "processing" ? "idle" : prev));
        recognitionRef.current = null;
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error("Failed to start speech recognition:", err);
      setStatus("error");
      setErrorMessage("Could not start voice recognition. Please try typing instead.");
    }
  }, [SpeechRecognitionClass, language, onTranscript]);

  useEffect(() => {
    langIndexRef.current = 0;
  }, [language]);

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {
          // Ignore abort on unmount
        }
      }
    };
  }, []);

  return {
    status,
    errorMessage,
    startListening,
    stopListening,
    clearError,
    isSupported,
  };
}
