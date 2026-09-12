import React from "react";
import type { AppTab, LanguageCode } from "../types";
import { useTranslation } from "../i18n";
import {
  SahkaarSetuLogo,
  HomeIcon,
  BellIcon,
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
  translationKey: string;
}> = [
  { id: "home", icon: HomeIcon, translationKey: "drawer.home" },
  { id: "notifications", icon: BellIcon, translationKey: "drawer.notifications" },
  { id: "ask", icon: MessageSquareIcon, translationKey: "drawer.ask" },
  { id: "services", icon: GridIcon, translationKey: "drawer.services" },
  { id: "grievance", icon: ClipboardCheckIcon, translationKey: "drawer.grievance" },
  { id: "history", icon: HistoryIcon, translationKey: "drawer.history" },
];

export const SideDrawer: React.FC<Props> = ({
  isOpen,
  onClose,
  activeTab,
  onSelectTab,
  language,
}) => {
  const t = useTranslation(language);

  if (!isOpen) return null;

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div className="drawer-brand-row">
            <SahkaarSetuLogo size={44} />
            <div className="drawer-brand-text">
              <h2 className="drawer-brand-name">SahkaarSetu</h2>
              <span className="drawer-brand-tagline">{t("drawer.tagline")}</span>
            </div>
          </div>
          <button
            type="button"
            className="drawer-close-btn"
            onClick={onClose}
            aria-label={t("drawer.closeMenu")}
          >
            <XIcon size={20} />
          </button>
        </div>

        <nav className="drawer-nav">
          {NAV_ITEMS.map((item) => {
            const IconComp = item.icon;
            const label = t(item.translationKey);
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
                <IconComp size={20} color={isActive ? "#123B5D" : "#68757D"} />
                <span className="drawer-nav-label">{label}</span>
              </button>
            );
          })}
        </nav>

        <div className="drawer-footer">
          <p className="drawer-footer-text">{t("drawer.footer")}</p>
        </div>
      </aside>
    </div>
  );
};

export default SideDrawer;
