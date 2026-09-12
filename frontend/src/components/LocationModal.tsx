import React from "react";
import type { LanguageCode } from "../types";
import type { UserLocationData } from "../services/locationService";
import { useTranslation } from "../i18n";
import { MapPinIcon, XIcon, ShieldCheckIcon } from "./Icons";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  locationData: UserLocationData;
  onRefreshLocation: () => void;
  isDetecting: boolean;
  language?: LanguageCode;
}

export const LocationModal: React.FC<Props> = ({
  isOpen,
  onClose,
  locationData,
  onRefreshLocation,
  isDetecting,
  language = "en",
}) => {
  const t = useTranslation(language);

  if (!isOpen) return null;

  const isAvailable = locationData.status === "available";

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel location-modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-title">
            <MapPinIcon size={20} color="#0F6B68" />
            <h3>{t("location.title")}</h3>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label={t("common.close")}>
            <XIcon size={18} />
          </button>
        </div>

        <div className="modal-body">
          {isAvailable ? (
            <div className="location-info-card">
              <div className="location-main-text">
                {locationData.formattedAddress || locationData.displayName}
              </div>

              <div className="location-status-row">
                <ShieldCheckIcon size={16} color="#10B981" />
                <span className="status-enabled-text">{t("location.servicesEnabled")}</span>
              </div>
            </div>
          ) : (
            <div className="location-info-card location-info-card--unavailable">
              <div className="location-main-text location-main-text--error">
                {t("location.unavailable")}
              </div>
              <p className="location-sub-text">
                {t("location.enablePrompt")}
              </p>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button
            type="button"
            className="action-btn-primary"
            onClick={onRefreshLocation}
            disabled={isDetecting}
          >
            {isDetecting ? t("location.detecting") : isAvailable ? t("location.update") : t("location.enable")}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LocationModal;
