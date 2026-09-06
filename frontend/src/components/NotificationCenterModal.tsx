import React from "react";
import { BellIcon, XIcon, ShieldCheckIcon } from "./Icons";

export interface NotificationItem {
  id: string;
  title: string;
  category: "Scheme" | "PACS" | "Insurance" | "System";
  message: string;
  timestamp: string;
  read: boolean;
  linkAction?: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  notifications: NotificationItem[];
  onMarkAllRead: () => void;
}

export const NotificationCenterModal: React.FC<Props> = ({
  isOpen,
  onClose,
  notifications,
  onMarkAllRead,
}) => {
  if (!isOpen) return null;

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-panel notification-modal-panel"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div className="modal-header-title">
            <BellIcon size={20} color="#126B62" />
            <h3>Notifications</h3>
            {unreadCount > 0 && (
              <span className="unread-count-badge">{unreadCount}</span>
            )}
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close"
          >
            <XIcon size={18} />
          </button>
        </div>

        <div className="modal-body notification-modal-body">
          {notifications.length === 0 ? (
            <div className="notification-empty-state">
              <ShieldCheckIcon size={36} color="#126B62" />
              <h4>You're all caught up.</h4>
              <p>Important cooperative updates, scheme notifications, and PACS alerts will appear here.</p>
            </div>
          ) : (
            <div className="notification-list">
              {notifications.map((item) => (
                <div
                  key={item.id}
                  className={`notification-card ${
                    !item.read ? "notification-card--unread" : ""
                  }`}
                >
                  <div className="notification-card-header">
                    <span className="notification-category-tag">
                      {item.category}
                    </span>
                    <span className="notification-time">{item.timestamp}</span>
                  </div>
                  <h5 className="notification-title">{item.title}</h5>
                  <p className="notification-message">{item.message}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {notifications.length > 0 && unreadCount > 0 && (
          <div className="modal-footer">
            <button
              type="button"
              className="action-btn-secondary"
              onClick={onMarkAllRead}
            >
              Mark all as read
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
