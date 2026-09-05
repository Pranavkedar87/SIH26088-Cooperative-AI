import React, { useState } from "react";
import type { SourceItem } from "../types";

interface Props {
  sources: SourceItem[];
}

const SourcesAccordion: React.FC<Props> = ({ sources }) => {
  const [open, setOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources-accordion">
      <button
        type="button"
        className="sources-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label={`${open ? "Collapse" : "Expand"} verified sources`}
      >
        <span className="sources-toggle__icon" aria-hidden="true">📚</span>
        <span className="sources-toggle__label">
          Verified Sources ({sources.length})
        </span>
        <span className="sources-toggle__chevron" aria-hidden="true">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open && (
        <ul className="sources-list">
          {sources.map((s, idx) => (
            <li key={idx} className="source-item">
              <span className="source-verified" aria-hidden="true">✓</span>
              <div className="source-content">
                <strong className="source-name">{s.title}</strong>
                {s.source_name && (
                  <span className="source-authority"> — {s.source_name}</span>
                )}
                {s.source_url && (
                  <a
                    href={s.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-link"
                  >
                    Official Link ↗
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SourcesAccordion;
