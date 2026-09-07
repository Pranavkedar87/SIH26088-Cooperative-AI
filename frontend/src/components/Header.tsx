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
  onOpenMenu: () => void;
  onOpenLocation: () => void;
  onOpenNotifications: () => void;
  onOpenLanguage: () => void;
}

export const Header: React.FC<Props> = ({
  language,
  locationData,
  unreadNotificationCount,
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

  const tagline =
    language === "hi"
      ? "बहुभाषी सहकार सहायता मंच"
      : language === "mr"
      ? "बहुभाषिक सहकार मदत व्यासपीठ"
      : "Multilingual Cooperative Assistance Platform";

  return (
    <header className="sahkaar-header" role="banner">
      {/* Institutional Top Accent Bar */}
      <div className="gov-top-bar">
        <div className="gov-top-bar__container">
          <span className="gov-top-bar__emblem">भारत सरकार | Government of India</span>
          <span className="gov-top-bar__ministry">सहकार मंत्रालय | Ministry of Cooperation</span>
        </div>
      </div>

      <div className="header-container">
        {/* Left: Brand & Service Identity */}
        <div className="header-left">
          <button
            type="button"
            className="header-icon-btn menu-toggle-btn"
            onClick={onOpenMenu}
            aria-label="Open Navigation Menu"
          >
            <MenuIcon size={20} color="#123B5D" />
          </button>

          <div className="header-brand-box" onClick={onOpenMenu} role="button" tabIndex={0}>
            <div className="header-logo-wrapper">
              <SahkaarSetuLogo size={26} color="#0F6B68" />
            </div>
            <div className="header-brand-titles">
              <h1 className="header-brand-name">SAHKAARSETU</h1>
              <span className="header-brand-tagline">{tagline}</span>
            </div>
          </div>
        </div>

        {/* Right: Operational Controls */}
        <div className="header-right">
          {/* Live Location Selector */}
          <button
            type="button"
            className="header-location-pill"
            onClick={onOpenLocation}
            title={locationData.displayName}
            aria-label={`Current jurisdiction: ${displayLocationText}`}
          >
            <MapPinIcon size={15} color="#0F6B68" />
            <span className="header-location-text">{displayLocationText}</span>
          </button>

          {/* Official Notifications */}
          <button
            type="button"
            className="header-icon-btn notification-bell-btn"
            onClick={onOpenNotifications}
            aria-label="View Official Notifications"
          >
            <BellIcon size={18} color="#123B5D" />
            {unreadNotificationCount > 0 && (
              <span className="header-notification-badge">
                {unreadNotificationCount > 9 ? "9+" : unreadNotificationCount}
              </span>
            )}
          </button>

          {/* Language Selector */}
          <button
            type="button"
            className="header-icon-btn language-trigger-btn"
            onClick={onOpenLanguage}
            aria-label="Change Portal Language"
          >
            <GlobeIcon size={18} color="#123B5D" />
            <span className="language-badge-text">{language.toUpperCase()}</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
