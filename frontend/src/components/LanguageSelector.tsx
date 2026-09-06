import React, { useState } from "react";
import type { LanguageCode } from "../types";
import { LANGUAGES } from "../types";
import { GlobeIcon, XIcon, CheckIcon } from "./Icons";

interface Props {
  selected: LanguageCode;
  onChange: (code: LanguageCode) => void;
  isOpen: boolean;
  onClose: () => void;
}

export const LanguageModal: React.FC<Props> = ({
  selected,
  onChange,
  isOpen,
  onClose,
}) => {
  const [searchQuery, setSearchQuery] = useState("");

  if (!isOpen) return null;

  const filteredLanguages = LANGUAGES.filter((lang) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      lang.label.toLowerCase().includes(q) ||
      lang.nativeLabel.toLowerCase().includes(q) ||
      lang.code.toLowerCase().includes(q)
    );
  });

  const handleSelect = (code: LanguageCode) => {
    onChange(code);
    onClose();
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-panel language-modal-panel"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div className="modal-header-title">
            <GlobeIcon size={20} color="#126B62" />
            <h3>भाषा चुनें / Select Language</h3>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close"
          >
            <XIcon size={18} />
          </button>
        </div>

        <div className="language-search-bar">
          <input
            type="text"
            className="language-search-input"
            placeholder="Search language / भाषा खोजें..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="modal-body language-modal-body">
          <div className="language-grid">
            {filteredLanguages.map((lang) => {
              const isSelected = selected === lang.code;
              return (
                <button
                  key={lang.code}
                  type="button"
                  className={`language-option-card ${
                    isSelected ? "language-option-card--selected" : ""
                  }`}
                  onClick={() => handleSelect(lang.code)}
                >
                  <div className="language-option-text">
                    <span className="language-native-name">{lang.nativeLabel}</span>
                    <span className="language-english-name">{lang.label}</span>
                  </div>
                  {isSelected && (
                    <div className="language-checkmark">
                      <CheckIcon size={18} color="#126B62" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LanguageModal;
