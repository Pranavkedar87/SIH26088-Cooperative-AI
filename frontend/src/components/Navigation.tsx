import React from "react";
import type { AppTab, LanguageCode } from "../types";

interface Props {
  activeTab: AppTab;
  onTabChange: (tab: AppTab) => void;
  language: LanguageCode;
}

const TAB_LABELS: Record<AppTab, { en: string; hi: string; mr: string; icon: string }> = {
  home: { en: "Home", hi: "मुख्य पृष्ठ", mr: "मुख्य पृष्ठ", icon: "🏠" },
  ask: { en: "Ask AI", hi: "प्रश्न पूछें", mr: "प्रश्न विचारा", icon: "💬" },
  services: { en: "Services", hi: "सेवाएं", mr: "सेवा", icon: "🏛️" },
  grievance: { en: "Grievance", hi: "शिकायत", mr: "तक्रार", icon: "📋" },
  history: { en: "History", hi: "इतिहास", mr: "इतिहास", icon: "🕒" },
};

const Navigation: React.FC<Props> = ({ activeTab, onTabChange, language }) => {
  const tabs: AppTab[] = ["home", "ask", "services", "grievance", "history"];

  return (
    <nav className="app-nav" aria-label="Main Navigation">
      <div className="nav-container">
        {tabs.map((tab) => {
          const meta = TAB_LABELS[tab];
          const label = meta[language] ?? meta.en;
          const isActive = activeTab === tab;

          return (
            <button
              key={tab}
              type="button"
              className={`nav-item ${isActive ? "nav-item--active" : ""}`}
              onClick={() => onTabChange(tab)}
              aria-selected={isActive}
              role="tab"
            >
              <span className="nav-item__icon" aria-hidden="true">
                {meta.icon}
              </span>
              <span className="nav-item__label">{label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default Navigation;
