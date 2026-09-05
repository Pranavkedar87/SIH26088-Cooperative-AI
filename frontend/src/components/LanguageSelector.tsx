import React from "react";
import type { Language, LanguageCode } from "../types";
import { LANGUAGES } from "../types";

interface Props {
  selected: LanguageCode;
  onChange: (code: LanguageCode) => void;
}

const LanguageSelector: React.FC<Props> = ({ selected, onChange }) => {
  return (
    <div className="segmented-lang-control" role="group" aria-label="Select Language">
      {LANGUAGES.map((lang: Language) => (
        <button
          key={lang.code}
          type="button"
          className={`segmented-lang-btn ${selected === lang.code ? "segmented-lang-btn--selected" : ""}`}
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
