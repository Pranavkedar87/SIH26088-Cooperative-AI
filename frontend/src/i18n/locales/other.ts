import type { LanguageCode } from "../../types";
import { hi } from "./hi";

// For regional languages that share base roots or Devanagari scripts,
// we provide customized or base-derived translations with appropriate localized titles
export const kok: Record<string, string> = {
  ...hi,
  "welcome.title": "सहकारसेतूंत तुमचें येवकार",
  "welcome.selectLanguage": "भास वेंचून काढा / Select Language",
  "nav.home": "घर",
  "nav.askAI": "विचार करा",
  "nav.voice": "उಲवून विचारात",
  "nav.camera": "कॅमेरा",
  "nav.grievance": "तक्रार",
  "drawer.tagline": "तुमचो सहकारी सांगाती",
  "common.continue": "मुखार वचा",
  "common.back": "फाटीं",
  "common.next": "फुडलें",
  "common.cancel": "रद्द करा",
  "common.done": "जालें",
};

export const sa: Record<string, string> = {
  ...hi,
  "welcome.title": "सहकारसेतौ स्वागतम्",
  "welcome.selectLanguage": "भाषां चिनुत / Select Language",
  "nav.home": "गृहम्",
  "nav.askAI": "पृच्छतु",
  "nav.voice": "वचनेन पृच्छतु",
  "nav.camera": "चित्रग्राहिणी",
  "nav.grievance": "अभियोगः",
  "drawer.tagline": "भवतः सहकारी सहचरः",
  "common.continue": "अनुवर्तताम्",
  "common.back": "प्रतिगच्छतु",
  "common.next": "अग्रिमम्",
  "common.cancel": "निरस्यताम्",
  "common.done": "पूर्णम्",
};

export const mai: Record<string, string> = {
  ...hi,
  "welcome.title": "सहकारसेतू में अपनेक स्वागत अछि",
  "welcome.selectLanguage": "भाषा चुनू / Select Language",
  "nav.home": "गृह",
  "nav.askAI": "प्रश्न पूछू",
  "nav.voice": "बाज के पूछू",
  "nav.camera": "कैमरा",
  "nav.grievance": "शिकायत",
  "drawer.tagline": "अहाँक सहकारी साथी",
  "common.continue": "आगाँ बढ़ू",
  "common.back": "पाछाँ",
  "common.next": "अगिला",
  "common.cancel": "रद्द करू",
  "common.done": "संपन्न",
};

export const ne: Record<string, string> = {
  ...hi,
  "welcome.title": "सहकारसेतुमा स्वागत छ",
  "welcome.selectLanguage": "भाषा छान्नुहोस् / Select Language",
  "nav.home": "गृह",
  "nav.askAI": "सोध्नुहोस्",
  "nav.voice": "बोलेर सोध्नुहोस्",
  "nav.camera": "क्यामेरा",
  "nav.grievance": "गुनासो",
  "drawer.tagline": "तपाईंको सहकारी साथी",
  "common.continue": "अगाडि बढ्नुहोस्",
  "common.back": "पछाडि",
  "common.next": "अर्को",
  "common.cancel": "रद्द गर्नुहोस्",
  "common.done": "सम्पन्न",
};

export const ks: Record<string, string> = {
  ...hi,
  "welcome.title": "سہکار سیتو منٛز خوش آمدید",
  "welcome.selectLanguage": "زبان ژاریو / Select Language",
  "nav.home": "گھر",
  "nav.askAI": "پرژھیو",
  "nav.voice": "بولیتھ پرژھیو",
  "nav.camera": "کیمرہ",
  "nav.grievance": "شکایتھ",
  "common.continue": "برونٛہہ پکِو",
  "common.back": "پتھکن",
  "common.cancel": "منسوخ",
};

export const sd: Record<string, string> = {
  ...hi,
  "welcome.title": "سهڪار سيتو ۾ ڀلي ڪري آيا",
  "welcome.selectLanguage": "ٻولي چونڊيو / Select Language",
  "nav.home": "گھر",
  "nav.askAI": "پڇو",
  "nav.voice": "ڳالهائي پڇو",
  "nav.camera": "ڪيمرا",
  "nav.grievance": "شکایت",
  "common.continue": "اڳتي وڌو",
  "common.back": "پوئتي",
  "common.cancel": "رد ڪريو",
};

export const mni: Record<string, string> = {
  ...hi,
  "welcome.title": "সহকারসেতুদা তরাম্না ওকচরি",
  "welcome.selectLanguage": "লোন খনবীয়ু / Select Language",
  "common.continue": "মখাতাবা",
  "common.back": "হন্না",
  "common.cancel": "তোকপা",
};

export const brx: Record<string, string> = {
  ...hi,
  "welcome.title": "सहकारसेतुआव बरायबाय",
  "welcome.selectLanguage": "राव सायख' / Select Language",
  "common.continue": "थांगासिनो था",
  "common.back": "उनाव",
  "common.cancel": "नेवसि",
};

export const sat: Record<string, string> = {
  ...hi,
  "welcome.title": "ᱥᱟᱦᱠᱟᱨᱥᱮᱛᱩ ᱨᱮ ᱥᱟᱹᱜᱩᱱ ᱫᱟᱨᱟᱢ",
  "welcome.selectLanguage": "ᱯᱟᱹᱨᱥᱤ ᱵᱟᱪᱷᱟᱣ ᱢᱮ / Select Language",
  "common.continue": "ᱞᱟᱦᱟᱜ ᱢᱮ",
  "common.back": "ᱛᱟᱭᱚᱢ",
  "common.cancel": "ᱵᱟᱹᱜᱤ ᱢᱮ",
};

export const OTHER_LANGUAGES: Partial<Record<LanguageCode, Record<string, string>>> = {
  kok,
  sa,
  mai,
  ne,
  ks,
  sd,
  mni,
  brx,
  sat,
};
