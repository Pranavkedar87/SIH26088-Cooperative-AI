import React from "react";
import type { AppTab, LanguageCode } from "../types";
import {
  HomeIcon,
  MessageSquareIcon,
  GridIcon,
  ClipboardCheckIcon,
} from "./Icons";

interface Props {
  activeTab: AppTab;
  onTabChange: (tab: AppTab) => void;
  language: LanguageCode;
}

const TAB_CONFIG: Array<{
  id: AppTab;
  icon: React.FC<{ size?: number; color?: string }>;
  en: string;
  hi: string;
  mr: string;
}> = [
  { id: "home", icon: HomeIcon, en: "Home", hi: "गृह", mr: "मुख्य" },
  { id: "ask", icon: MessageSquareIcon, en: "Ask AI", hi: "प्रश्न पूछें", mr: "प्रश्न विचारा" },
  { id: "services", icon: GridIcon, en: "Services", hi: "सेवाएं", mr: "सेवा" },
  { id: "grievance", icon: ClipboardCheckIcon, en: "Grievance", hi: "शिकायत", mr: "तक्रार" },
];

const Navigation: React.FC<Props> = ({ activeTab, onTabChange, language }) => {
  return (
    <nav className="app-nav" aria-label="Primary Navigation">
      <div className="nav-container">
        {TAB_CONFIG.map((tab) => {
          const IconComp = tab.icon;
          const label = (tab as any)[language] ?? tab.en;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              type="button"
              className={`nav-item ${isActive ? "nav-item--active" : ""}`}
              onClick={() => onTabChange(tab.id)}
              aria-selected={isActive}
              role="tab"
            >
              <div className="nav-item__icon-wrapper">
                <IconComp size={20} color={isActive ? "#176B5B" : "#66777A"} />
              </div>
              <span className="nav-item__label">{label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default Navigation;
