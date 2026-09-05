import { useState, useCallback, useRef, useEffect } from "react";
import type { LanguageCode, STTStatus } from "../types";

const STT_LANG_MAP: Record<LanguageCode, string[]> = {
  en: ["en-IN", "en-US", "en"],
  hi: ["hi-IN", "hi", "en-IN"],
  mr: ["mr-IN", "mr", "hi-IN", "en-IN"],
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

  // Keep latest onTranscript in ref to prevent startListening recreation loops
  const onTranscriptRef = useRef(onTranscript);
  useEffect(() => {
    onTranscriptRef.current = onTranscript;
  }, [onTranscript]);

  const SpeechRecognitionClass =
    typeof window !== "undefined"
      ? window.SpeechRecognition || window.webkitSpeechRecognition
      : null;

  const isSupported = Boolean(SpeechRecognitionClass);

  const clearError = useCallback(() => {
    setErrorMessage(null);
    setStatus("idle");
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onstart = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
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
    langIndexRef.current = 0; // Reset language fallback index on explicit user request

    if (!SpeechRecognitionClass) {
      setStatus("unsupported");
      setErrorMessage("Voice input is not supported in this browser. You can type your question instead.");
      return;
    }

    // Clean up any existing recognition instance to avoid InvalidStateError
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onstart = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.abort();
      } catch (e) {
        // Ignore abort errors
      }
      recognitionRef.current = null;
    }

    const targetLangs = STT_LANG_MAP[language] || ["en-IN"];
    const currentLang = targetLangs[langIndexRef.current % targetLangs.length];

    try {
      const recognition = new SpeechRecognitionClass();
      recognition.lang = currentLang;
      recognition.continuous = false;
      recognition.interimResults = false;

      // Optimistically indicate listening so mic UI immediately responds
      setStatus("listening");

      recognition.onstart = () => {
        setStatus("listening");
      };

      recognition.onresult = (event: any) => {
        setStatus("processing");
        if (event.results && event.results[0] && event.results[0][0]) {
          const text = event.results[0][0].transcript;
          if (text && text.trim()) {
            onTranscriptRef.current(text.trim());
          }
        }
        setStatus("idle");
      };

      recognition.onerror = (event: any) => {
        const err = event.error;
        console.warn("Speech recognition error:", err, "lang:", currentLang);

        if (err === "permission-denied") {
          setStatus("error");
          setErrorMessage("Microphone permission denied. Please allow microphone access in your browser settings.");
          return;
        }

        // If current language code failed and we have fallback language codes available, retry
        if (langIndexRef.current < targetLangs.length - 1) {
          langIndexRef.current += 1;
          console.info("Retrying STT with fallback language code:", targetLangs[langIndexRef.current]);
          setTimeout(() => startListening(), 50);
          return;
        }

        if (err === "not-allowed") {
          setStatus("error");
          setErrorMessage("Microphone access not allowed. Check browser permissions.");
        } else if (err === "no-speech") {
          setStatus("error");
          setErrorMessage("No speech detected. Click mic to try speaking again.");
        } else if (err === "language-not-supported" || err === "service-not-allowed") {
          setStatus("error");
          if (err === "service-not-allowed") {
            setErrorMessage("Safari requires Dictation enabled (System Settings → Keyboard → Dictation). For best multi-lingual voice support, use Google Chrome.");
          } else {
            setErrorMessage("Selected language is not supported by your browser. Try Google Chrome or type your question.");
          }
        } else if (err === "audio-capture") {
          setStatus("error");
          setErrorMessage("No microphone detected. Please connect a microphone and try again.");
        } else if (err === "aborted") {
          setStatus("idle");
        } else {
          setStatus("error");
          setErrorMessage("Voice input unavailable. You can type your question instead.");
        }
      };

      recognition.onend = () => {
        setStatus((prev) => (prev === "listening" || prev === "processing" ? "idle" : prev));
        recognitionRef.current = null;
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error("Failed to start speech recognition synchronously:", err);
      if (langIndexRef.current < targetLangs.length - 1) {
        langIndexRef.current += 1;
        setTimeout(() => startListening(), 50);
        return;
      }
      setStatus("error");
      setErrorMessage("Could not start voice recognition. Please try typing instead.");
    }
  }, [SpeechRecognitionClass, language]);


  useEffect(() => {
    langIndexRef.current = 0;
    setErrorMessage(null);
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onstart = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.abort();
      } catch (e) {
        // Ignore abort on language change
      }
      recognitionRef.current = null;
    }
    setStatus("idle");
  }, [language]);


  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.onstart = null;
          recognitionRef.current.onresult = null;
          recognitionRef.current.onerror = null;
          recognitionRef.current.onend = null;
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

