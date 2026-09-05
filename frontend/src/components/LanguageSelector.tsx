import React from "react";
import type { LanguageCode } from "../types";
import { LANGUAGES } from "../types";
import { ChevronRightIcon } from "./Icons";

interface Props {
  selected: LanguageCode;
  onChange: (code: LanguageCode) => void;
}

const LanguageSelector: React.FC<Props> = ({ selected, onChange }) => {
  return (
    <div className="compact-lang-dropdown">
      <select
        className="lang-select-input"
        value={selected}
        onChange={(e) => onChange(e.target.value as LanguageCode)}
        aria-label="Select Language"
      >
        {LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.nativeLabel}
          </option>
        ))}
      </select>
      <span className="lang-select-arrow">
        <ChevronRightIcon size={12} />
      </span>
    </div>
  );
};

export default LanguageSelector;
