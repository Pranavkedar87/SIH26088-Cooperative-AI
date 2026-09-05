import React, { useState, useCallback, useEffect } from "react";
import type { ChatMessage, LanguageCode, AppTab, HistoryItem } from "./types";
import { sendQuery } from "./api/client";
import { useTextToSpeech } from "./hooks/useTextToSpeech";
import { useSpeechRecognition } from "./hooks/useSpeechRecognition";
import LanguageSelector from "./components/LanguageSelector";
import Navigation from "./components/Navigation";
import AssistanceHub from "./components/AssistanceHub";
import GuidedAssistance from "./components/GuidedAssistance";
import ServicesDirectory from "./components/ServicesDirectory";
import GrievanceWorkflow from "./components/GrievanceWorkflow";
import ChatArea from "./components/ChatArea";
import ChatInput from "./components/ChatInput";
import { SahkaarSetuLogo } from "./components/Icons";
import "./App.css";

let _id = 0;
function uid(): string {
  return `msg-${Date.now()}-${++_id}`;
}

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AppTab>("home");
  const [language, setLanguage] = useState<LanguageCode>("en");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Active guided flow ID (e.g. "crop_damage", "pacs_help")
  const [activeGuidedFlow, setActiveGuidedFlow] = useState<string | null>(null);

  // Local storage history
  const [history, setHistory] = useState<HistoryItem[]>(() => {
    try {
      const saved = localStorage.getItem("sahkaarsetu_history");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem("sahkaarsetu_history", JSON.stringify(history));
    } catch {
      // Ignore quota errors
    }
  }, [history]);

  const { activeId, speak } = useTextToSpeech();

  const addMessage = useCallback((msg: ChatMessage) => {
    setMessages((prev) => [...prev, msg]);
  }, []);

  const saveHistoryItem = useCallback(
    (title: string, subtitle: string, details?: string, type: "query" | "grievance" | "guided" = "query") => {
      const newItem: HistoryItem = {
        id: `hist-${Date.now()}`,
        type,
        title,
        subtitle,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        language,
        details,
      };
      setHistory((prev) => [newItem, ...prev.slice(0, 19)]);
    },
    [language]
  );

  const handleSendQuery = useCallback(
    async (text: string) => {
      setError(null);
      setActiveTab("ask");

      addMessage({
        id: uid(),
        role: "user",
        content: text,
        timestamp: new Date(),
        language,
      });

      setIsLoading(true);
      saveHistoryItem(text.slice(0, 45) + (text.length > 45 ? "…" : ""), "User Query", undefined, "query");

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
          intent: response.intent,
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
    [language, sessionId, addMessage, saveHistoryItem]
  );

  // STT Hook for Homepage Voice shortcut
  const handleVoiceTranscript = useCallback(
    (text: string) => {
      if (text.trim()) {
        handleSendQuery(text.trim());
      }
    },
    [handleSendQuery]
  );

  const { status: sttStatus, startListening, stopListening } = useSpeechRecognition({
    language,
    onTranscript: handleVoiceTranscript,
  });

  const handleMicClick = () => {
    if (sttStatus === "listening") {
      stopListening();
    } else {
      startListening();
    }
  };

  const handleStartGuided = (flowId: string) => {
    setActiveGuidedFlow(flowId);
  };

  const handleGuidedAskAI = (prompt: string) => {
    setActiveGuidedFlow(null);
    handleSendQuery(prompt);
  };

  return (
    <div className="platform-app">
      {/* Clean Institutional Header (NO "Live" Badge, NO Emojis) */}
      <header className="platform-header">
        <div className="header-brand-block">
          <div className="header-brand-row">
            <SahkaarSetuLogo size={28} color="#176B5B" />
            <h1 className="brand-name">SahkaarSetu</h1>
          </div>
          <span className="brand-tagline">
            {language === "hi"
              ? "आपका सहकारी साथी"
              : language === "mr"
              ? "तुमचा सहकारी साथी"
              : "Your Cooperative Companion"}
          </span>
        </div>

        {/* Segmented Language Selector */}
        <div className="header-controls">
          <LanguageSelector selected={language} onChange={setLanguage} />
        </div>
      </header>

      {/* Main Multi-Tab Viewport */}
      <main className="platform-main">
        {/* Error Notification Bar */}
        {error && (
          <div className="platform-error-bar" role="alert">
            <span>{error}</span>
            <button
              type="button"
              className="error-dismiss-btn"
              onClick={() => setError(null)}
            >
              ×
            </button>
          </div>
        )}

        {/* Tab 1: HOME Assistance Hub */}
        {activeTab === "home" && !activeGuidedFlow && (
          <AssistanceHub
            language={language}
            onStartAsk={(query) => {
              if (query) handleSendQuery(query);
              else setActiveTab("ask");
            }}
            onSelectGuided={handleStartGuided}
            onSelectService={() => setActiveTab("services")}
            isListening={sttStatus === "listening"}
            onMicClick={handleMicClick}
          />
        )}

        {/* Guided Assistance Overlay/View */}
        {activeGuidedFlow && (
          <GuidedAssistance
            flowType={activeGuidedFlow}
            language={language}
            onAskAI={handleGuidedAskAI}
            onBack={() => setActiveGuidedFlow(null)}
          />
        )}

        {/* Tab 2: ASK AI Chat Assistant */}
        {activeTab === "ask" && (
          <div className="chat-tab-container">
            <ChatArea
              messages={messages}
              isLoading={isLoading}
              language={language}
              onSpeak={speak}
              activeSpeakingId={activeId}
              onFollowUp={(p) => setInputValue(p)}
              onSimplify={(p) => handleSendQuery(p)}
            />
          </div>
        )}

        {/* Tab 3: SERVICES Domain Directory */}
        {activeTab === "services" && (
          <ServicesDirectory
            language={language}
            onAskAI={(prompt) => handleSendQuery(prompt)}
          />
        )}

        {/* Tab 4: GRIEVANCE Workflow */}
        {activeTab === "grievance" && (
          <GrievanceWorkflow
            language={language}
            onSaveHistory={(title, sub, details) => {
              saveHistoryItem(title, sub, details, "grievance");
            }}
          />
        )}
      </main>

      {/* Single Sticky Input Bar (Shown during Ask Tab or when messages exist) */}
      {(activeTab === "ask" || messages.length > 0) && (
        <ChatInput
          language={language}
          isLoading={isLoading}
          onSend={handleSendQuery}
          value={inputValue}
          onChange={setInputValue}
        />
      )}

      {/* Persistent 4-Tab Navigation Bar */}
      <Navigation
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveGuidedFlow(null);
          setActiveTab(tab);
        }}
        language={language}
      />
    </div>
  );
};

export default App;
