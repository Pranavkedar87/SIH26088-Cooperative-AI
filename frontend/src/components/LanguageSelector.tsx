import React from "react";
import type { Language, LanguageCode } from "../types";
import { LANGUAGES } from "../types";

interface Props {
  selected: LanguageCode;
  onChange: (code: LanguageCode) => void;
}

const LanguageSelector: React.FC<Props> = ({ selected, onChange }) => {
  return (
    <div className="lang-selector" role="group" aria-label="Select language">
      {LANGUAGES.map((lang: Language) => (
        <button
          key={lang.code}
          className={`lang-btn${selected === lang.code ? " lang-btn--active" : ""}`}
          onClick={() => onChange(lang.code)}
          aria-pressed={selected === lang.code}
        >
          {lang.nativeLabel}
        </button>
      ))}
    </div>
  );
};

export default LanguageSelector;
