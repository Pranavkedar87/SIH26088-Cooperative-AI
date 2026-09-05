import { useState, useCallback, useEffect, useRef } from "react";
import type { LanguageCode } from "../types";

const LANG_VOICE_PREFERENCES: Record<string, string[]> = {
  en: ["en-IN", "en-US", "en-GB", "en"],
  hi: ["hi-IN", "hi", "en-IN"],
  mr: ["mr-IN", "mr", "hi-IN", "hi", "en-IN"], // Fallback to Hindi voice if Marathi voice is missing
  ta: ["ta-IN", "ta", "hi-IN", "en-IN"],
  te: ["te-IN", "te", "hi-IN", "en-IN"],
  kn: ["kn-IN", "kn", "hi-IN", "en-IN"],
  gu: ["gu-IN", "gu", "hi-IN", "en-IN"],
  bn: ["bn-IN", "bn", "hi-IN", "en-IN"],
  pa: ["pa-IN", "pa", "hi-IN", "en-IN"],
  ml: ["ml-IN", "ml", "hi-IN", "en-IN"],
};

interface UseTextToSpeechReturn {
  activeId: string | null;
  isSpeaking: boolean;
  speak: (id: string, text: string, language: LanguageCode) => void;
  stop: () => void;
  unlockAudio: () => void;
  isSupported: boolean;
}

export function useTextToSpeech(): UseTextToSpeechReturn {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const isSupported = typeof window !== "undefined" && "speechSynthesis" in window;

  const unlockAudio = useCallback(() => {
    if (isSupported && window.speechSynthesis) {
      try {
        window.speechSynthesis.resume();
        const dummy = new SpeechSynthesisUtterance("");
        dummy.volume = 0;
        window.speechSynthesis.speak(dummy);
      } catch (e) {
        // ignore unlock errors
      }
    }
  }, [isSupported]);

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
        console.warn("[TTS] Speech Synthesis is not supported in this browser.");
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

      const bestVoice = findBestVoice(language, voices);
      const preferredLangCode = LANG_VOICE_PREFERENCES[language]?.[0] || "en-IN";

      console.info(`[TTS] Request started | lang: ${language} | text len: ${cleanText.length} | voice: ${bestVoice?.name || preferredLangCode}`);

      try {
        window.speechSynthesis.resume();

        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = bestVoice ? bestVoice.lang : preferredLangCode;

        if (bestVoice) {
          utterance.voice = bestVoice;
        }

        utterance.onstart = () => {
          console.info("[TTS] Audio playback started.");
          setActiveId(id);
          setIsSpeaking(true);
        };

        utterance.onend = () => {
          console.info("[TTS] Audio playback completed.");
          setActiveId(null);
          setIsSpeaking(false);
          currentUtteranceRef.current = null;
        };

        utterance.onerror = (e) => {
          console.warn("[TTS] Playback error or interrupted:", e);
          setActiveId(null);
          setIsSpeaking(false);
          currentUtteranceRef.current = null;
        };

        currentUtteranceRef.current = utterance;
        setActiveId(id);
        setIsSpeaking(true);

        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.error("[TTS] Failed to execute TTS speak:", err);
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
    unlockAudio,
    isSupported,
  };
}
