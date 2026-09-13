/**
 * AssistanceSlipView.tsx
 * Citizen Phase 3A.3 — 58mm Thermal-Printer-Friendly Assistance Slip & QR Verification
 * SahkaarSetu / Cooperative AI (SIH26088)
 */
import React, { useMemo } from "react";
import type { AssistanceSlipData, LanguageCode } from "../types";
import { useTranslation } from "../i18n";
import { generateQrSvg } from "../utils/qrGenerator";
import {
  LandmarkIcon,
  PrinterIcon,
  XIcon,
} from "./Icons";

interface Props {
  slipData: AssistanceSlipData;
  language: LanguageCode;
  onClose?: () => void;
  isModal?: boolean;
}

export const AssistanceSlipView: React.FC<Props> = ({
  slipData,
  language,
  onClose,
  isModal = true,
}) => {
  const t = useTranslation(language);

  const handlePrint = () => {
    window.print();
  };

  const formattedDate = (() => {
    try {
      const d = new Date(slipData.created_at);
      if (isNaN(d.getTime())) return slipData.created_at;
      return d.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      });
    } catch {
      return slipData.created_at;
    }
  })();

  const qrSvg = useMemo(() => {
    try {
      return generateQrSvg(slipData.qr_payload, {
        size: 120,
        margin: 2,
        fgColor: "#000000",
        bgColor: "#FFFFFF",
      });
    } catch (err) {
      console.warn("[ASSISTANCE_SLIP] QR generation fallback:", err);
      return null;
    }
  }, [slipData.qr_payload]);

  const content = (
    <div className="slip-view-wrapper">
      {/* Screen Toolbar (Hidden on Print) */}
      <div className="slip-toolbar slip-no-print">
        <div className="slip-toolbar-left">
          <LandmarkIcon size={20} color="#123B5D" />
          <span className="slip-toolbar-title">{t("slip.title")}</span>
        </div>
        <div className="slip-toolbar-actions">
          <button
            type="button"
            className="slip-btn-print"
            onClick={handlePrint}
            aria-label={t("slip.printBtn")}
          >
            <PrinterIcon size={16} />
            <span>{t("slip.printBtn")}</span>
          </button>
          {onClose && (
            <button
              type="button"
              className="slip-btn-close"
              onClick={onClose}
              aria-label={t("common.close")}
            >
              <XIcon size={16} />
              <span>{t("common.close")}</span>
            </button>
          )}
        </div>
      </div>

      {/* 58mm Thermal Printable Slip Area */}
      <div id="pacs-assistance-slip" className="pacs-assistance-slip">
        {/* Receipt Header */}
        <div className="slip-header">
          <div className="slip-emblem">🏛️</div>
          <div className="slip-header-title">{slipData.header}</div>
          <div className="slip-header-sub">{t("slip.subtitle")}</div>
          <div className="slip-divider-dashed" />
        </div>

        {/* Prominent Reference Code */}
        <div className="slip-ref-box">
          <div className="slip-ref-label">{t("slip.refCode")}</div>
          <div className="slip-ref-value">{slipData.reference_code}</div>
          <div className="slip-timestamp">{formattedDate}</div>
        </div>

        <div className="slip-divider-dashed" />

        {/* Metadata Grid */}
        <div className="slip-meta-table">
          <div className="slip-meta-row">
            <span className="slip-meta-key">{t("slip.pacs")}:</span>
            <span className="slip-meta-val slip-meta-val--bold">
              {slipData.pacs_name}
            </span>
          </div>

          {slipData.village && (
            <div className="slip-meta-row">
              <span className="slip-meta-key">{t("slip.village")}:</span>
              <span className="slip-meta-val">{slipData.village}</span>
            </div>
          )}

          <div className="slip-meta-row">
            <span className="slip-meta-key">{t("slip.category")}:</span>
            <span className="slip-meta-val slip-category-badge">
              {slipData.category}
            </span>
          </div>

          <div className="slip-meta-row">
            <span className="slip-meta-key">{t("slip.citizen")}:</span>
            <span className="slip-meta-val">
              {slipData.citizen_masked_name}
            </span>
          </div>

          <div className="slip-meta-row">
            <span className="slip-meta-key">{t("slip.phone")}:</span>
            <span className="slip-meta-val">
              {slipData.citizen_phone_masked}
            </span>
          </div>

          <div className="slip-meta-row">
            <span className="slip-meta-key">{t("slip.languages")}:</span>
            <span className="slip-meta-val">
              {slipData.citizen_language.toUpperCase()} →{" "}
              {slipData.officer_language.toUpperCase()}
            </span>
          </div>
        </div>

        <div className="slip-divider-dashed" />

        {/* Citizen Issue / Original Query */}
        <div className="slip-section">
          <div className="slip-section-title">{t("slip.originalQuery")}</div>
          <div className="slip-section-body slip-query-text">
            {slipData.original_query}
          </div>
        </div>

        {/* Officer Translated Note (if translated) */}
        {slipData.officer_translated_note && (
          <div className="slip-section">
            <div className="slip-section-header-row">
              <span className="slip-section-title">{t("slip.officerNote")}</span>
              <span className="slip-bhashini-tag">
                {t("slip.bhashiniNotice")}
              </span>
            </div>
            <div className="slip-section-body slip-translated-text">
              {slipData.officer_translated_note}
            </div>
          </div>
        )}

        {/* Grounded AI Guidance */}
        {slipData.ai_guidance_summary && (
          <div className="slip-section">
            <div className="slip-section-title">{t("slip.aiGuidance")}</div>
            <div className="slip-section-body slip-guidance-text">
              {slipData.ai_guidance_summary}
            </div>
          </div>
        )}

        {/* Verified Citations */}
        {slipData.sources && slipData.sources.length > 0 && (
          <div className="slip-section">
            <div className="slip-section-title">{t("slip.sources")}</div>
            <ul className="slip-sources-list">
              {slipData.sources.slice(0, 3).map((src, idx) => (
                <li key={idx} className="slip-source-item">
                  • {src}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="slip-divider-dashed" />

        {/* Verification QR Code */}
        <div className="slip-qr-box">
          <div className="slip-qr-graphic">
            {qrSvg ? (
              <div
                className="slip-qr-svg-wrapper"
                dangerouslySetInnerHTML={{ __html: qrSvg }}
              />
            ) : (
              <div className="qr-fallback">QR Preview Unavailable</div>
            )}
          </div>
          <div className="slip-qr-notice">{t("slip.qrScanNotice")}</div>
          <div className="slip-qr-privacy">{t("slip.qrPrivacyNotice")}</div>
        </div>

        <div className="slip-divider-dashed" />

        {/* Statutory Facilitation Disclaimer */}
        <div className="slip-disclaimer">
          <p>{slipData.disclaimer || t("slip.disclaimer")}</p>
        </div>

        {/* Footer cutoff indicator */}
        <div className="slip-footer-cutoff">
          <span>--- END OF REFERENCE SLIP ---</span>
        </div>
      </div>
    </div>
  );

  if (isModal) {
    return (
      <div
        className="slip-modal-backdrop"
        role="dialog"
        aria-modal="true"
        aria-labelledby="slip-modal-title"
      >
        <div className="slip-modal-container">{content}</div>
      </div>
    );
  }

  return content;
};

export default AssistanceSlipView;
