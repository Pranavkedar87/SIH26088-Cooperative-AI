import React from "react";
import type { UserLocationData } from "../services/locationService";
import { MapPinIcon, XIcon, ShieldCheckIcon } from "./Icons";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  locationData: UserLocationData;
  onRefreshLocation: () => void;
  isDetecting: boolean;
}

export const LocationModal: React.FC<Props> = ({
  isOpen,
  onClose,
  locationData,
  onRefreshLocation,
  isDetecting,
}) => {
  if (!isOpen) return null;

  const isAvailable = locationData.status === "available";

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel location-modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-title">
            <MapPinIcon size={20} color="#126B62" />
            <h3>Your Location</h3>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close">
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
                <span className="status-enabled-text">Location services ● Enabled</span>
              </div>
            </div>
          ) : (
            <div className="location-info-card location-info-card--unavailable">
              <div className="location-main-text location-main-text--error">
                Location unavailable
              </div>
              <p className="location-sub-text">
                Enable location access to get more relevant cooperative assistance and regional schemes.
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
            {isDetecting ? "Detecting location..." : isAvailable ? "Update Location" : "Enable Location"}
          </button>
        </div>
      </div>
    </div>
  );
};
