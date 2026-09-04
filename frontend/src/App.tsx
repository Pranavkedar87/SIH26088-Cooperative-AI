import React, { useState, useCallback } from "react";
import type { ChatMessage, LanguageCode } from "./types";
import { sendQuery } from "./api/client";
import LanguageSelector from "./components/LanguageSelector";
import QuickTopics from "./components/QuickTopics";
import ChatArea from "./components/ChatArea";
import ChatInput from "./components/ChatInput";
import "./App.css";

// ── Locale strings ────────────────────────────────────────────────────────────

const WELCOME: Record<LanguageCode, { heading: string; subheading: string }> = {
  en: {
    heading: "Cooperative AI Assistant",
    subheading:
      "Get instant guidance on cooperative laws, government schemes, PACS, PMFBY, and more.",
  },
  hi: {
    heading: "सहकारी AI सहायक",
    subheading:
      "सहकारी कानूनों, सरकारी योजनाओं, पैक्स, पीएमएफबीवाई और अन्य विषयों पर तुरंत मार्गदर्शन प्राप्त करें।",
  },
  mr: {
    heading: "सहकारी AI सहाय्यक",
    subheading:
      "सहकारी कायदे, सरकारी योजना, पॅक्स, पीएमएफबीवाय आणि इतर विषयांवर त्वरित मार्गदर्शन मिळवा.",
  },
};

// ── Unique ID helper ──────────────────────────────────────────────────────────

let _id = 0;
function uid(): string {
  return `msg-${Date.now()}-${++_id}`;
}

// ── App ───────────────────────────────────────────────────────────────────────

const App: React.FC = () => {
  const [language, setLanguage] = useState<LanguageCode>("en");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addMessage = useCallback((msg: ChatMessage) => {
    setMessages((prev) => [...prev, msg]);
  }, []);

  const handleSend = useCallback(
    async (text: string) => {
      setError(null);

      // Add user message immediately
      addMessage({
        id: uid(),
        role: "user",
        content: text,
        timestamp: new Date(),
        language,
      });

      setIsLoading(true);

      try {
        const response = await sendQuery({ message: text, language });

        addMessage({
          id: uid(),
          role: "assistant",
          content: response.answer,
          timestamp: new Date(),
          language: response.language,
        });
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Something went wrong.";
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    },
    [language, addMessage]
  );

  const handleTopicSelect = useCallback(
    (prompt: string) => {
      setInputValue(prompt);
    },
    []
  );

  const locale = WELCOME[language];

  return (
    <div className="app">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-brand">
          <span className="header-logo" aria-hidden="true">🤝</span>
          <div className="header-title-group">
            <h1 className="header-title">{locale.heading}</h1>
            <p className="header-subtitle">SIH 2026 — Cooperative Governance</p>
          </div>
        </div>
        <LanguageSelector selected={language} onChange={setLanguage} />
      </header>

      {/* ── Main ───────────────────────────────────────────────────────── */}
      <main className="app-main">
        {/* Welcome banner — shown only when no messages yet */}
        {messages.length === 0 && (
          <div className="welcome-banner">
            <p className="welcome-text">{locale.subheading}</p>
          </div>
        )}

        {/* Quick topics */}
        <QuickTopics language={language} onSelect={handleTopicSelect} />

        {/* Error bar */}
        {error && (
          <div className="error-bar" role="alert">
            ⚠️ {error}
            <button className="error-dismiss" onClick={() => setError(null)} aria-label="Dismiss error">
              ×
            </button>
          </div>
        )}

        {/* Conversation */}
        <ChatArea messages={messages} isLoading={isLoading} language={language} />
      </main>

      {/* ── Input ──────────────────────────────────────────────────────── */}
      <footer className="app-footer">
        <ChatInput
          language={language}
          isLoading={isLoading}
          onSend={handleSend}
          value={inputValue}
          onChange={setInputValue}
        />
        <p className="footer-note">
          Powered by Gemini AI · Government of India · SIH 2026
        </p>
      </footer>
    </div>
  );
};

export default App;
