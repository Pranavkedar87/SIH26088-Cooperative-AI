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
  speak: (id: string, text: string, language: LanguageCode, onEnd?: () => void) => void;
  stop: () => void;
  unlockAudio: () => void;
  isSupported: boolean;
}

export function useTextToSpeech(options?: { onEnd?: () => void }): UseTextToSpeechReturn {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const onEndRef = useRef<(() => void) | undefined>(options?.onEnd);

  useEffect(() => {
    onEndRef.current = options?.onEnd;
  }, [options?.onEnd]);

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
    // Recognized female voice identifiers across Chrome, Safari, Edge, Android, iOS & Windows
    const femaleRegex = /female|woman|lady|swara|zira|samantha|victoria|heera|aditi|kalpana|neerja|jenny|aria|shreya|raveena|veena|kiran|sonia|ananya|wavenet-a|wavenet-c|wavenet-d|standard-a|standard-c/i;

    // 1. First priority: Exact language match WITH explicit female voice signature
    for (const pref of preferences) {
      const femaleMatch = availableVoices.find(
        (v) =>
          (v.lang.toLowerCase() === pref.toLowerCase() || v.lang.toLowerCase().startsWith(pref.toLowerCase())) &&
          femaleRegex.test(v.name)
      );
      if (femaleMatch) return femaleMatch;
    }

    // 2. Second priority: Any matching language voice
    for (const pref of preferences) {
      const match = availableVoices.find(
        (v) => v.lang.toLowerCase() === pref.toLowerCase() || v.lang.toLowerCase().startsWith(pref.toLowerCase())
      );
      if (match) return match;
    }

    // 3. Third priority: Any available female voice in system
    const fallbackFemale = availableVoices.find((v) => femaleRegex.test(v.name));
    if (fallbackFemale) return fallbackFemale;

    return availableVoices[0] || null;
  }, []);

  const speak = useCallback(
    (id: string, text: string, language: LanguageCode, onEndCall?: () => void) => {
      if (!isSupported) {
        console.warn("[TTS] Speech Synthesis is not supported in this browser.");
        if (onEndCall) onEndCall();
        else if (onEndRef.current) onEndRef.current();
        return;
      }

      // If clicking the currently speaking message, stop it
      if (activeId === id && isSpeaking) {
        stop();
        return;
      }

      // Cancel any ongoing speech
      stop();

      if (!text || !text.trim()) {
        if (onEndCall) onEndCall();
        else if (onEndRef.current) onEndRef.current();
        return;
      }

      // Clean text: strip markdown formatting or link tags before speaking
      const cleanText = text
        .replace(/https?:\/\/\S+/g, "")
        .replace(/[\*\_\`\#]/g, "")
        .replace(/^\s*[-*+]\s+/gm, "")
        .replace(/^\s*\d+\.\s+/gm, "")
        .trim();

      if (!cleanText) {
        if (onEndCall) onEndCall();
        else if (onEndRef.current) onEndRef.current();
        return;
      }

      const bestVoice = findBestVoice(language, voices);
      const preferredLangCode = LANG_VOICE_PREFERENCES[language]?.[0] || "en-IN";

      console.info(`[TTS] Request started | lang: ${language} | text len: ${cleanText.length} | female voice: ${bestVoice?.name || preferredLangCode}`);

      try {
        window.speechSynthesis.resume();

        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = bestVoice ? bestVoice.lang : preferredLangCode;

        if (bestVoice) {
          utterance.voice = bestVoice;
        }

        // Configure warm female voice parameters
        utterance.pitch = 1.1; // Warm, natural female voice pitch
        utterance.rate = 0.95;  // Slightly relaxed rate for clear regional speech

        utterance.onstart = () => {
          console.info("[TTS] Audio playback started.");
          setActiveId(id);
          setIsSpeaking(true);
        };

        utterance.onend = () => {
          console.info("[TTS] Audio playback completed naturally.");
          setActiveId(null);
          setIsSpeaking(false);
          currentUtteranceRef.current = null;
          if (onEndCall) {
            onEndCall();
          } else if (onEndRef.current) {
            onEndRef.current();
          }
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
        if (onEndCall) onEndCall();
        else if (onEndRef.current) onEndRef.current();
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
