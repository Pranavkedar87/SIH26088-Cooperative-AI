import React from "react";
import type { AppTab, LanguageCode } from "../types";
import {
  SahkaarSetuLogo,
  HomeIcon,
  MessageSquareIcon,
  GridIcon,
  ClipboardCheckIcon,
  HistoryIcon,
  XIcon,
} from "./Icons";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  activeTab: AppTab;
  onSelectTab: (tab: AppTab) => void;
  language: LanguageCode;
}

const NAV_ITEMS: Array<{
  id: AppTab;
  icon: React.FC<{ size?: number; color?: string }>;
  en: string;
  hi: string;
  mr: string;
}> = [
  { id: "home", icon: HomeIcon, en: "Home Hub", hi: "गृह केंद्र", mr: "मुख्य केंद्र" },
  { id: "ask", icon: MessageSquareIcon, en: "Ask AI Assistant", hi: "प्रश्न पूछें", mr: "प्रश्न विचारा" },
  { id: "services", icon: GridIcon, en: "Services Directory", hi: "सेवा निर्देशिका", mr: "सेवा निर्देशिका" },
  { id: "grievance", icon: ClipboardCheckIcon, en: "Grievance Portal", hi: "शिकायत पोर्टल", mr: "तक्रार निवारण" },
  { id: "history", icon: HistoryIcon, en: "Query History", hi: "इतिहास", mr: "इतिहास" },
];

export const SideDrawer: React.FC<Props> = ({
  isOpen,
  onClose,
  activeTab,
  onSelectTab,
  language,
}) => {
  if (!isOpen) return null;

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div className="drawer-brand-row">
            <SahkaarSetuLogo size={28} color="#126B62" />
            <div className="drawer-brand-text">
              <h2 className="drawer-brand-name">SahkaarSetu</h2>
              <span className="drawer-brand-tagline">
                {language === "hi"
                  ? "आपका सहकारी साथी"
                  : language === "mr"
                  ? "तुमचा सहकारी साथी"
                  : "Your Cooperative Companion"}
              </span>
            </div>
          </div>
          <button type="button" className="drawer-close-btn" onClick={onClose} aria-label="Close menu">
            <XIcon size={20} />
          </button>
        </div>

        <nav className="drawer-nav">
          {NAV_ITEMS.map((item) => {
            const IconComp = item.icon;
            const label = item[language as "en" | "hi" | "mr"] || item.en;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                type="button"
                className={`drawer-nav-item ${isActive ? "drawer-nav-item--active" : ""}`}
                onClick={() => {
                  onSelectTab(item.id);
                  onClose();
                }}
              >
                <IconComp size={20} color={isActive ? "#126B62" : "#4A5568"} />
                <span className="drawer-nav-label">{label}</span>
              </button>
            );
          })}
        </nav>

        <div className="drawer-footer">
          <p className="drawer-footer-text">
            Official Multilingual Cooperative Governance Platform
          </p>
        </div>
      </aside>
    </div>
  );
};
