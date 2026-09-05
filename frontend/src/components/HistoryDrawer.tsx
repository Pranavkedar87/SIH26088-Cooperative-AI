import React from "react";
import type { HistoryItem, LanguageCode } from "../types";

interface Props {
  history: HistoryItem[];
  language: LanguageCode;
  onClear: () => void;
  onSelect: (item: HistoryItem) => void;
}

const HistoryDrawer: React.FC<Props> = ({ history, language, onClear, onSelect }) => {
  return (
    <div className="history-drawer" aria-label="My Assistance History">
      <div className="history-header">
        <div className="history-title-group">
          <h3 className="history-title">
            🕒 {language === "hi" ? "मेरी सहायता इतिहास" : language === "mr" ? "माझा सहाय्य इतिहास" : "My Assistance History"}
          </h3>
          <p className="history-sub">
            {language === "hi"
              ? "हाल ही में देखे गए विषय और सहेजे गए शिकायत सारांश"
              : language === "mr"
              ? "नुकतेच पाहिलेले विषय व जतन केलेले तक्रार सारांश"
              : "Recent help, saved guidance cards, and grievance drafts"}
          </p>
        </div>
        {history.length > 0 && (
          <button type="button" className="history-clear-btn" onClick={onClear}>
            {language === "hi" ? "इतिहास साफ़ करें" : language === "mr" ? "इतिहास साफ करा" : "Clear History"}
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <div className="history-empty">
          <span className="history-empty-icon">📁</span>
          <p>
            {language === "hi"
              ? "कोई सहेजा गया इतिहास नहीं है। आपके द्वारा पूछे गए प्रश्न यहाँ दिखाई देंगे।"
              : language === "mr"
              ? "कोणताही जतन केलेला इतिहास नाही. तुमचे प्रश्न येथे दिसतील."
              : "No recent history yet. Queries and grievance drafts will be saved locally here."}
          </p>
        </div>
      ) : (
        <div className="history-list">
          {history.map((item) => (
            <div key={item.id} className="history-card" onClick={() => onSelect(item)}>
              <div className="history-card__type-tag">
                {item.type === "grievance" ? "📋 Grievance" : item.type === "guided" ? "🌾 Guided" : "💬 Query"}
              </div>
              <h4 className="history-card__title">{item.title}</h4>
              <p className="history-card__sub">{item.subtitle}</p>
              <span className="history-card__time">{item.timestamp}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HistoryDrawer;
