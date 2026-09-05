import React from "react";
import type { Language, LanguageCode } from "../types";
import { LANGUAGES } from "../types";

interface Props {
  selected: LanguageCode;
  onChange: (code: LanguageCode) => void;
}

const LanguageSelector: React.FC<Props> = ({ selected, onChange }) => {
  return (
    <div className="segmented-lang-bar" role="group" aria-label="Language Selector">
      {LANGUAGES.map((lang: Language) => {
        const isSelected = selected === lang.code;
        const displayLabel = lang.code === "en" ? "EN" : lang.nativeLabel;

        return (
          <button
            key={lang.code}
            type="button"
            className={`segmented-lang-segment ${isSelected ? "segmented-lang-segment--active" : ""}`}
            onClick={() => onChange(lang.code)}
            aria-pressed={isSelected}
          >
            {displayLabel}
          </button>
        );
      })}
    </div>
  );
};

export default LanguageSelector;
