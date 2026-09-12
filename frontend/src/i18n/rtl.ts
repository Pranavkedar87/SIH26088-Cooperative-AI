import type { LanguageCode } from "../types";

export const RTL_LANGUAGES: Set<LanguageCode> = new Set(["ur", "ks", "sd"]);

export function isRTL(lang: LanguageCode): boolean {
  return RTL_LANGUAGES.has(lang);
}
