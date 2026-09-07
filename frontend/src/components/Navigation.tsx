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
  { id: "home", icon: HomeIcon, en: "Home", hi: "मुख्य पृष्ठ", mr: "मुख्य पृष्ठ" },
  { id: "ask", icon: MessageSquareIcon, en: "Guidance", hi: "मार्गदर्शन", mr: "मार्गदर्शन" },
  { id: "services", icon: GridIcon, en: "Services", hi: "सेवाएं", mr: "सेवा" },
  { id: "grievance", icon: ClipboardCheckIcon, en: "Grievance", hi: "तक्रार / शिकायत", mr: "तक्रार निवारण" },
];

export const Navigation: React.FC<Props> = ({ activeTab, onTabChange, language }) => {
  return (
    <nav className="app-nav" aria-label="Primary Navigation" role="navigation">
      <div className="nav-container" role="tablist">
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
              aria-label={label}
            >
              <div className="nav-item__icon-wrapper">
                <IconComp size={18} color={isActive ? "#123B5D" : "#4A5D6E"} />
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
