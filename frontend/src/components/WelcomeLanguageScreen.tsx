import React, { useState } from "react";
import type { LanguageCode } from "../types";
import { LANGUAGES } from "../types";

interface Props {
  initialLanguage: LanguageCode;
  onConfirm: (lang: LanguageCode) => void;
}

export const WelcomeLanguageScreen: React.FC<Props> = ({
  initialLanguage = "en",
  onConfirm,
}) => {
  const [selectedLang, setSelectedLang] = useState<LanguageCode>(initialLanguage);

  return (
    <div className="welcome-lang-canvas" role="region" aria-label="Welcome and Language Selection">
      <div className="welcome-lang-container">
        {/* Top Welcome Title */}
        <h1 className="welcome-main-title">Welcome to SahkaarSetu</h1>

        {/* Farmer & Wife Illustration */}
        <div className="welcome-illustration-box">
          <img
            src="/welcome-farmer.png"
            alt="Namaste - Welcome from Indian Farmer and Wife"
            className="welcome-farmer-img"
          />
        </div>

        {/* Subtitle / Prompt */}
        <h2 className="welcome-select-title">Select Language / भाषा चुनें</h2>

        {/* 2-Column Language Grid */}
        <div className="welcome-lang-grid">
          {LANGUAGES.map((lang) => {
            const isSelected = selectedLang === lang.code;
            return (
              <button
                key={lang.code}
                type="button"
                className={`welcome-lang-card ${
                  isSelected ? "welcome-lang-card--active" : ""
                }`}
                onClick={() => setSelectedLang(lang.code)}
                aria-pressed={isSelected}
              >
                <span className="welcome-lang-native">{lang.nativeLabel}</span>
                <span className="welcome-lang-english">{lang.label}</span>
              </button>
            );
          })}
        </div>

        {/* Bottom Floating/Sticky Action Bar */}
        <div className="welcome-bottom-bar">
          <button
            type="button"
            className="welcome-continue-btn"
            onClick={() => onConfirm(selectedLang)}
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
};

export default WelcomeLanguageScreen;
