import React, { useState, useCallback } from "react";
import type { ChatMessage, LanguageCode } from "./types";
import { sendQuery } from "./api/client";
import { useTextToSpeech } from "./hooks/useTextToSpeech";
import LanguageSelector from "./components/LanguageSelector";
import QuickTopics from "./components/QuickTopics";
import ChatArea from "./components/ChatArea";
import ChatInput from "./components/ChatInput";
import WelcomeHero from "./components/WelcomeHero";
import DomainCards from "./components/DomainCards";
import "./App.css";

// ── Unique ID helper ──────────────────────────────────────────────────────────

let _id = 0;
function uid(): string {
  return `msg-${Date.now()}-${++_id}`;
}

// ── SAHKAARSETU logo SVG (inline, no external image needed) ──────────────────

const LogoSVG: React.FC = () => (
  <svg
    className="header-logo-svg"
    viewBox="0 0 36 36"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    {/* Cooperative circle */}
    <circle cx="18" cy="18" r="16" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
    {/* Handshake */}
    <path d="M11 21 Q9 17 12 14 L16 11 Q18 10 20 13 L18 16" stroke="#fff" strokeWidth="2" strokeLinecap="round" fill="none" />
    <path d="M25 21 Q27 17 24 14 L20 11 Q18 10 16 13 L18 16" stroke="rgba(255,200,100,0.9)" strokeWidth="2" strokeLinecap="round" fill="none" />
    <ellipse cx="18" cy="18" rx="4" ry="3.5" fill="rgba(255,255,255,0.2)" stroke="#fff" strokeWidth="1.2" />
    {/* Wheat dots */}
    <circle cx="9" cy="23" r="1.5" fill="rgba(255,200,100,0.8)" />
    <circle cx="27" cy="23" r="1.5" fill="rgba(255,200,100,0.8)" />
  </svg>
);

// ── App ───────────────────────────────────────────────────────────────────────

const App: React.FC = () => {
  const [language, setLanguage] = useState<LanguageCode>("en");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const { activeId, speak } = useTextToSpeech();

  const addMessage = useCallback((msg: ChatMessage) => {
    setMessages((prev) => [...prev, msg]);
  }, []);

  const handleSend = useCallback(
    async (text: string) => {
      setError(null);

      addMessage({
        id: uid(),
        role: "user",
        content: text,
        timestamp: new Date(),
        language,
      });

      setIsLoading(true);

      try {
        const response = await sendQuery({
          message: text,
          language,
          session_id: sessionId,
        });

        if (response.session_id) {
          setSessionId(response.session_id);
        }

        addMessage({
          id: uid(),
          role: "assistant",
          content: response.answer,
          timestamp: new Date(),
          language: response.language,
          sources: response.sources,
        });
      } catch (err) {
        const isNetwork =
          err instanceof TypeError && err.message.toLowerCase().includes("fetch");
        const msg = isNetwork
          ? "📡 Connection error — please check your internet connection and try again."
          : err instanceof Error
          ? err.message
          : "Something went wrong. Please try again.";
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    },
    [language, sessionId, addMessage]
  );

  const handleTopicSelect = useCallback((prompt: string) => {
    setInputValue(prompt);
  }, []);

  const handleFollowUp = useCallback((prompt: string) => {
    setInputValue(prompt);
  }, []);

  const showWelcome = messages.length === 0 && !isLoading;

  return (
    <div className="app">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-brand">
          <LogoSVG />
          <div className="header-title-group">
            <h1 className="header-title">SAHKAARSETU</h1>
            <p className="header-tagline">Ask · Understand · Act</p>
          </div>
        </div>
        <LanguageSelector selected={language} onChange={setLanguage} />
      </header>

      {/* ── Main ───────────────────────────────────────────────────────── */}
      <main className="app-main">
        {/* Welcome hero + domain cards — shown only before first message */}
        {showWelcome && (
          <>
            <WelcomeHero language={language} onSelect={handleTopicSelect} />

            <div className="domain-cards-section">
              <p className="domain-cards-title">Explore Topics</p>
              <DomainCards language={language} onSelect={handleTopicSelect} />
            </div>
          </>
        )}

        {/* Quick topic chips — always visible */}
        {!showWelcome && (
          <div className="quick-topics-section">
            <QuickTopics language={language} onSelect={handleTopicSelect} />
          </div>
        )}

        {/* Error bar */}
        {error && (
          <div className="error-bar" role="alert">
            {error}
            <button
              className="error-dismiss"
              onClick={() => setError(null)}
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        )}

        {/* Conversation */}
        {messages.length > 0 || isLoading ? (
          <ChatArea
            messages={messages}
            isLoading={isLoading}
            language={language}
            onSpeak={speak}
            activeSpeakingId={activeId}
            onFollowUp={handleFollowUp}
          />
        ) : null}
      </main>

      {/* ── Footer / Input ──────────────────────────────────────────────── */}
      <footer className="app-footer">
        <ChatInput
          language={language}
          isLoading={isLoading}
          onSend={handleSend}
          value={inputValue}
          onChange={setInputValue}
        />
        <p className="footer-note">
          Powered by Gemini AI · Verified knowledge base · SIH 2026
        </p>
      </footer>
    </div>
  );
};

export default App;
