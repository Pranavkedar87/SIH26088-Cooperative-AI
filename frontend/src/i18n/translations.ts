import type { LanguageCode } from "../types";
import { en } from "./locales/en";
import { hi } from "./locales/hi";
import { mr } from "./locales/mr";
import { gu } from "./locales/gu";
import { bn } from "./locales/bn";
import { ta } from "./locales/ta";
import { te } from "./locales/te";
import { kn } from "./locales/kn";
import { ml } from "./locales/ml";
import { pa } from "./locales/pa";
import { or } from "./locales/or";
import { as } from "./locales/as";
import { ur } from "./locales/ur";
import { OTHER_LANGUAGES } from "./locales/other";

export const UI_TRANSLATIONS: Record<LanguageCode, Record<string, string>> = {
  en,
  hi,
  mr,
  gu,
  bn,
  ta,
  te,
  kn,
  ml,
  pa,
  or,
  as,
  ur,
  sa: OTHER_LANGUAGES.sa ?? hi,
  ks: OTHER_LANGUAGES.ks ?? hi,
  kok: OTHER_LANGUAGES.kok ?? hi,
  mai: OTHER_LANGUAGES.mai ?? hi,
  mni: OTHER_LANGUAGES.mni ?? hi,
  ne: OTHER_LANGUAGES.ne ?? hi,
  brx: OTHER_LANGUAGES.brx ?? hi,
  sat: OTHER_LANGUAGES.sat ?? hi,
  sd: OTHER_LANGUAGES.sd ?? hi,
};
