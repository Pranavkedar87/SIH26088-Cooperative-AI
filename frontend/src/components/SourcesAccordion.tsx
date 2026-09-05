import React, { useState } from "react";
import type { SourceItem } from "../types";
import { CheckVerifiedIcon, ExternalLinkIcon } from "./Icons";

interface Props {
  sources: SourceItem[];
}

const SourcesAccordion: React.FC<Props> = ({ sources }) => {
  const [open, setOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources-block">
      <button
        type="button"
        className="sources-block__toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label={`${open ? "Hide" : "Show"} verified sources`}
      >
        <CheckVerifiedIcon size={14} color="#2A7B4C" />
        <span className="sources-block__label">
          VERIFIED SOURCES ({sources.length})
        </span>
        <span className="sources-block__arrow" aria-hidden="true">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open && (
        <ul className="sources-block__list">
          {sources.map((s, idx) => (
            <li key={idx} className="sources-block__item">
              <div className="sources-block__meta">
                <span className="sources-block__doc-title">{s.title}</span>
                {s.source_name && (
                  <span className="sources-block__authority"> — {s.source_name}</span>
                )}
              </div>
              {s.source_url && (
                <a
                  href={s.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="sources-block__link"
                >
                  <span>View official source</span>
                  <ExternalLinkIcon size={13} color="#145A62" />
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
