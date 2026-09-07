import React from "react";
import type { LanguageCode } from "../types";
import type { UserLocationData } from "../services/locationService";
import {
  MenuIcon,
  SahkaarSetuLogo,
  MapPinIcon,
  BellIcon,
  GlobeIcon,
} from "./Icons";

interface Props {
  language: LanguageCode;
  locationData: UserLocationData;
  unreadNotificationCount: number;
  hideNotificationBell?: boolean;
  onOpenMenu: () => void;
  onOpenLocation: () => void;
  onOpenNotifications: () => void;
  onOpenLanguage: () => void;
}

export const Header: React.FC<Props> = ({
  language,
  locationData,
  unreadNotificationCount,
  hideNotificationBell = false,
  onOpenMenu,
  onOpenLocation,
  onOpenNotifications,
  onOpenLanguage,
}) => {
  const displayLocationText =
    locationData.status === "detecting"
      ? "Detecting location..."
      : locationData.status === "available"
      ? locationData.shortDisplayName || locationData.displayName
      : "Location";

  return (
    <header className="sahkaar-header">
      <div className="header-container">
        {/* Left: Hamburger Menu & Brand */}
        <div className="header-left">
          <button
            type="button"
            className="header-icon-btn menu-toggle-btn"
            onClick={onOpenMenu}
            aria-label="Open Navigation Menu"
          >
            <MenuIcon size={22} color="#0F6B68" />
          </button>

          <div className="header-brand-box" onClick={onOpenMenu} role="button" tabIndex={0}>
            <SahkaarSetuLogo size={36} />
            <div className="header-brand-titles">
              <h1 className="header-brand-name">SahkaarSetu</h1>
              <span className="header-brand-tagline">Cooperative AI</span>
            </div>
          </div>
        </div>

        {/* Right: Controls (Location, Notifications, Language) */}
        <div className="header-right">
          {/* Live Location Pill Button */}
          <button
            type="button"
            className="header-location-pill"
            onClick={onOpenLocation}
            title={locationData.displayName}
            aria-label="View Location Details"
          >
            <MapPinIcon size={18} color="#0F6B68" />
            <span className="header-location-text">{displayLocationText}</span>
          </button>

          {/* Notification Bell Button (Hidden when already on notification page) */}
          {!hideNotificationBell && (
            <button
              type="button"
              className="header-icon-btn notification-bell-btn"
              onClick={onOpenNotifications}
              aria-label="View Notifications"
            >
              <BellIcon size={20} color="#0F6B68" />
              {unreadNotificationCount > 0 && (
                <span className="header-notification-badge">
                  {unreadNotificationCount > 9 ? "9+" : unreadNotificationCount}
                </span>
              )}
            </button>
          )}

          {/* Language Selector Trigger Button */}
          <button
            type="button"
            className="header-icon-btn language-trigger-btn"
            onClick={onOpenLanguage}
            aria-label="Change Language"
          >
            <GlobeIcon size={20} color="#0F6B68" />
            <span className="language-badge-text">{language.toUpperCase()}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
