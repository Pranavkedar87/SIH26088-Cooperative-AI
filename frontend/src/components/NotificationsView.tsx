import React, { useState } from "react";
import type { LanguageCode } from "../types";
import { useTranslation } from "../i18n";
import {
  BellIcon,
  CheckIcon,
  WheatIcon,
  LandmarkIcon,
  FileCheckIcon,
  ShieldCheckIcon,
  MessageSquareIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
} from "./Icons";

export interface NotificationItem {
  id: string;
  title: string;
  category: "Scheme" | "PACS" | "Insurance" | "System";
  message: string;
  timestamp: string;
  read: boolean;
  linkAction?: string;
  query?: string;
}

interface Props {
  language: LanguageCode;
  notifications: NotificationItem[];
  onMarkAllRead: () => void;
  onNotificationClick: (item: NotificationItem) => void;
  onAskAI: (query: string) => void;
  onBack?: () => void;
}

export const NotificationsView: React.FC<Props> = ({
  language = "en",
  notifications,
  onMarkAllRead,
  onNotificationClick,
  onAskAI,
  onBack,
}) => {
  const [filter, setFilter] = useState<string>("all");
  const t = useTranslation(language);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const filteredNotifications = notifications.filter((n) => {
    if (filter === "unread") return !n.read;
    if (filter === "Insurance") return n.category === "Insurance";
    if (filter === "PACS") return n.category === "PACS";
    if (filter === "Scheme") return n.category === "Scheme";
    return true;
  });

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "Insurance":
        return <WheatIcon size={18} color="#0F6B68" />;
      case "PACS":
        return <LandmarkIcon size={18} color="#0F6B68" />;
      case "Scheme":
        return <FileCheckIcon size={18} color="#0F6B68" />;
      default:
        return <BellIcon size={18} color="#0F6B68" />;
    }
  };

  return (
    <div className="notifications-tab-canvas" role="region" aria-label="Notifications Center">
      <div className="notifications-tab-container">
        {/* Top Back Navigation Bar */}
        {onBack && (
          <div className="notifications-top-nav-bar">
            <button
              type="button"
              className="notifications-back-btn"
              onClick={onBack}
              aria-label={t("common.back")}
            >
              <ArrowLeftIcon size={18} color="#0F6B68" />
              <span>{t("common.back")}</span>
            </button>
          </div>
        )}

        {/* Header Title Bar */}
        <div className="notifications-tab-header">
          <div className="notifications-header-left">
            <div className="notifications-header-icon-box">
              <BellIcon size={24} color="#0F6B68" />
              {unreadCount > 0 && <span className="notif-badge-pill">{unreadCount}</span>}
            </div>
            <div className="notifications-header-text">
              <h2 className="notifications-tab-title">{t("notifications.title")}</h2>
              <p className="notifications-tab-sub">{t("notifications.sub")}</p>
            </div>
          </div>

          {unreadCount > 0 && (
            <button
              type="button"
              className="mark-all-read-btn"
              onClick={onMarkAllRead}
              aria-label={t("notifications.markAllRead")}
            >
              <CheckIcon size={14} />
              <span>{t("notifications.markAllRead")}</span>
            </button>
          )}
        </div>

        {/* Filter Chips Bar */}
        <div className="notifications-filter-bar">
          <button
            type="button"
            className={`notif-filter-chip ${filter === "all" ? "notif-filter-chip--active" : ""}`}
            onClick={() => setFilter("all")}
          >
            {t("notifications.all")} ({notifications.length})
          </button>
          {unreadCount > 0 && (
            <button
              type="button"
              className={`notif-filter-chip ${filter === "unread" ? "notif-filter-chip--active" : ""}`}
              onClick={() => setFilter("unread")}
            >
              {t("notifications.unread")} ({unreadCount})
            </button>
          )}
          <button
            type="button"
            className={`notif-filter-chip ${filter === "Insurance" ? "notif-filter-chip--active" : ""}`}
            onClick={() => setFilter("Insurance")}
          >
            {t("notifications.filterInsurance")}
          </button>
          <button
            type="button"
            className={`notif-filter-chip ${filter === "PACS" ? "notif-filter-chip--active" : ""}`}
            onClick={() => setFilter("PACS")}
          >
            {t("notifications.filterPacs")}
          </button>
          <button
            type="button"
            className={`notif-filter-chip ${filter === "Scheme" ? "notif-filter-chip--active" : ""}`}
            onClick={() => setFilter("Scheme")}
          >
            {t("notifications.filterSchemes")}
          </button>
        </div>

        {/* Notifications Content List */}
        {filteredNotifications.length === 0 ? (
          <div className="notifications-empty-box">
            <div className="notif-empty-icon">
              <ShieldCheckIcon size={44} color="#0F6B68" />
            </div>
            <h3 className="notif-empty-title">{t("notifications.emptyTitle")}</h3>
            <p className="notif-empty-desc">{t("notifications.emptySub")}</p>
          </div>
        ) : (
          <div className="notifications-list-grid">
            {filteredNotifications.map((item) => (
              <article
                key={item.id}
                className={`notif-item-card ${!item.read ? "notif-item-card--unread" : ""}`}
                onClick={() => onNotificationClick(item)}
              >
                <div className="notif-item-top">
                  <div className="notif-item-category-row">
                    <div className="notif-item-icon-bubble">
                      {getCategoryIcon(item.category)}
                    </div>
                    <span className="notif-item-category-tag">{item.category}</span>
                    {!item.read && <span className="notif-item-unread-dot" />}
                  </div>
                  <span className="notif-item-time">{item.timestamp}</span>
                </div>

                <h4 className="notif-item-title">{item.title}</h4>
                <p className="notif-item-message">{item.message}</p>

                {/* Bottom Action */}
                <div className="notif-item-actions">
                  <button
                    type="button"
                    className="notif-ask-ai-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      onAskAI(item.query || item.title);
                    }}
                  >
                    <MessageSquareIcon size={14} color="#0F6B68" />
                    <span>{t("notifications.askAiBtn")}</span>
                    <ArrowRightIcon size={12} color="#0F6B68" />
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationsView;
