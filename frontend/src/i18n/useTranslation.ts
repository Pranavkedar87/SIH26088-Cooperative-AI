import { useMemo } from "react";
import type { LanguageCode } from "../types";
import { UI_TRANSLATIONS } from "./translations";

export function translate(language: LanguageCode, key: string, fallback?: string): string {
  const dict = UI_TRANSLATIONS[language] ?? UI_TRANSLATIONS.en;
  if (dict && dict[key] !== undefined) {
    return dict[key];
  }
  const enDict = UI_TRANSLATIONS.en;
  if (enDict && enDict[key] !== undefined) {
    return enDict[key];
  }
  return fallback !== undefined ? fallback : key;
}

export function useTranslation(language: LanguageCode) {
  return useMemo(() => {
    return (key: string, fallback?: string): string => {
      return translate(language, key, fallback);
    };
  }, [language]);
}
