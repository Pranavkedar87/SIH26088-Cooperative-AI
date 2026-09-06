import React, { useState, useEffect, useRef } from "react";
import type { LanguageCode } from "../types";
import { LANGUAGES } from "../types";
import { GlobeIcon, CheckIcon } from "./Icons";

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
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

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
    <div className="lang-dropdown-overlay" onClick={onClose}>
      <div
        ref={dropdownRef}
        className="lang-dropdown-popover"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Dropdown Header */}
        <div className="lang-dropdown-header">
          <span className="lang-dropdown-title">भाषा चुनें</span>
          <GlobeIcon size={18} color="#126B62" />
        </div>

        {/* Optional Search Bar */}
        <div className="lang-dropdown-search">
          <input
            type="text"
            className="lang-search-input"
            placeholder="Search language / भाषा खोजें..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            autoFocus
          />
        </div>

        {/* Vertical Scrollable List */}
        <div className="lang-dropdown-list">
          {filteredLanguages.map((lang) => {
            const isSelected = selected === lang.code;
            return (
              <button
                key={lang.code}
                type="button"
                className={`lang-dropdown-item ${
                  isSelected ? "lang-dropdown-item--selected" : ""
                }`}
                onClick={() => handleSelect(lang.code)}
              >
                <div className="lang-dropdown-item-labels">
                  <span className="lang-native-label">{lang.nativeLabel}</span>
                  <span className="lang-english-label">{lang.label}</span>
                </div>
                {isSelected && (
                  <div className="lang-selected-check">
                    <CheckIcon size={16} color="#FFFFFF" />
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default LanguageModal;

