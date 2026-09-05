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

let _id = 0;
function uid(): string {
  return `msg-${Date.now()}-${++_id}`;
}

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
          ? "Connection error — please check your network connection and try again."
          : err instanceof Error
          ? err.message
          : "An unexpected error occurred. Please try again.";
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
    <div className="civic-app">
      {/* Institutional Public Service Header */}
      <header className="civic-header">
        <div className="civic-header__brand">
          <div className="civic-header__title-row">
            <h1 className="civic-header__title">SAHKAARSETU</h1>
            <span className="online-badge" title="Service active">
              <span className="online-dot" /> Online
            </span>
          </div>
          <p className="civic-header__subtitle">
            AI-Powered Cooperative Assistance
          </p>
        </div>
        <LanguageSelector selected={language} onChange={setLanguage} />
      </header>

      {/* Main Workspace Container */}
      <main className="civic-main">
        {/* Welcome Section & Service Directory (Shown when no active chat) */}
        {showWelcome && (
          <div className="welcome-container">
            <WelcomeHero language={language} onSelect={handleTopicSelect} />

            <section className="services-section">
              <h3 className="services-section__title">EXPLORE SERVICES</h3>
              <DomainCards language={language} onSelect={handleTopicSelect} />
            </section>
          </div>
        )}

        {/* Quick topic navigation bar during active chat */}
        {!showWelcome && (
          <div className="active-topics-bar">
            <QuickTopics language={language} onSelect={handleTopicSelect} />
          </div>
        )}

        {/* Error Notification Bar */}
        {error && (
          <div className="civic-error-bar" role="alert">
            <span>⚠️ {error}</span>
            <button
              type="button"
              className="civic-error-dismiss"
              onClick={() => setError(null)}
              aria-label="Dismiss message"
            >
              ×
            </button>
          </div>
        )}

        {/* Conversation Viewport */}
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

      {/* Input Area & Quiet Footer */}
      <footer className="civic-footer">
        <ChatInput
          language={language}
          isLoading={isLoading}
          onSend={handleSend}
          value={inputValue}
          onChange={setInputValue}
        />
        <div className="civic-footer__note">
          SAHKAARSETU · Multilingual Cooperative Assistance Platform · Verified knowledge base · SIH 2026
        </div>
      </footer>
    </div>
  );
};

export default App;
