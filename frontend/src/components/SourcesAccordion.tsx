import React, { useState } from "react";
import type { SourceItem, LanguageCode } from "../types";
import { useTranslation } from "../i18n";
import { ShieldCheckIcon, ExternalLinkIcon } from "./Icons";

interface Props {
  sources: SourceItem[];
  language?: LanguageCode;
}

const SourcesAccordion: React.FC<Props> = ({ sources, language = "en" }) => {
  const [open, setOpen] = useState(false);
  const t = useTranslation(language);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources-drawer">
      <button
        type="button"
        className="sources-drawer__toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label={`${open ? t("sources.hide") : t("sources.show")} sources`}
      >
        <ShieldCheckIcon size={14} color="#2C6E8F" />
        <span className="sources-drawer__label">
          {t("sources.sourceBackedGuidance")} ({sources.length})
        </span>
        <span className="sources-drawer__arrow" aria-hidden="true">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open && (
        <ul className="sources-drawer__list">
          {sources.map((s, idx) => (
            <li key={idx} className="sources-drawer__item">
              <div className="sources-drawer__meta">
                <span className="sources-drawer__doc">{s.title}</span>
                {s.source_name && (
                  <span className="sources-drawer__authority"> — {s.source_name}</span>
                )}
              </div>
              {s.source_url && (
                <a
                  href={s.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="sources-drawer__link"
                >
                  <span>{t("sources.viewOfficialSource")}</span>
                  <ExternalLinkIcon size={12} color="#2C6E8F" />
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SourcesAccordion;
