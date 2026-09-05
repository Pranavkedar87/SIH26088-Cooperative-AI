import { useState, useCallback, useEffect, useRef } from "react";
import type { LanguageCode } from "../types";

const LANG_VOICE_PREFERENCES: Record<LanguageCode, string[]> = {
  en: ["en-IN", "en-US", "en-GB", "en"],
  hi: ["hi-IN", "hi"],
  mr: ["mr-IN", "mr", "hi-IN", "hi"], // Fallback to Hindi voice if Marathi voice is not installed
};

interface UseTextToSpeechReturn {
  activeId: string | null;
  isSpeaking: boolean;
  speak: (id: string, text: string, language: LanguageCode) => void;
  stop: () => void;
  isSupported: boolean;
}

export function useTextToSpeech(): UseTextToSpeechReturn {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const isSupported = typeof window !== "undefined" && "speechSynthesis" in window;

  // Load available voices
  useEffect(() => {
    if (!isSupported) return;

    const updateVoices = () => {
      const available = window.speechSynthesis.getVoices();
      setVoices(available);
    };

    updateVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = updateVoices;
    }
  }, [isSupported]);

  const stop = useCallback(() => {
    if (isSupported && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    currentUtteranceRef.current = null;
    setActiveId(null);
    setIsSpeaking(false);
  }, [isSupported]);

  const findBestVoice = useCallback((lang: LanguageCode, availableVoices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null => {
    const preferences = LANG_VOICE_PREFERENCES[lang] || ["en-IN", "en"];
    for (const pref of preferences) {
      const match = availableVoices.find(
        (v) => v.lang.toLowerCase() === pref.toLowerCase() || v.lang.toLowerCase().startsWith(pref.toLowerCase())
      );
      if (match) return match;
    }
    return availableVoices[0] || null;
  }, []);

  const speak = useCallback(
    (id: string, text: string, language: LanguageCode) => {
      if (!isSupported) {
        console.warn("Speech Synthesis is not supported in this browser.");
        return;
      }

      // If clicking the currently speaking message, stop it
      if (activeId === id && isSpeaking) {
        stop();
        return;
      }

      // Cancel any ongoing speech
      stop();

      if (!text || !text.trim()) return;

      // Clean text: strip markdown formatting or link tags before speaking
      const cleanText = text
        .replace(/https?:\/\/\S+/g, "")
        .replace(/[\*\_\`\#]/g, "")
        .trim();

      if (!cleanText) return;

      try {
        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        const preferredLangCode = LANG_VOICE_PREFERENCES[language]?.[0] || "en-IN";
        utterance.lang = preferredLangCode;

        const bestVoice = findBestVoice(language, voices);
        if (bestVoice) {
          utterance.voice = bestVoice;
        }

        utterance.onend = () => {
          setActiveId(null);
          setIsSpeaking(false);
          currentUtteranceRef.current = null;
        };

        utterance.onerror = (e) => {
          console.warn("TTS error:", e);
          setActiveId(null);
          setIsSpeaking(false);
          currentUtteranceRef.current = null;
        };

        currentUtteranceRef.current = utterance;
        setActiveId(id);
        setIsSpeaking(true);

        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.error("Failed to execute TTS:", err);
        stop();
      }
    },
    [isSupported, activeId, isSpeaking, voices, findBestVoice, stop]
  );

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    activeId,
    isSpeaking,
    speak,
    stop,
    isSupported,
  };
}
