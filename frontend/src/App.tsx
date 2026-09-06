import React, { useState, useCallback, useEffect } from "react";
import type { ChatMessage, LanguageCode, AppTab, HistoryItem } from "./types";
import { sendQuery } from "./api/client";
import { useTextToSpeech } from "./hooks/useTextToSpeech";
import { Header } from "./components/Header";
import { SideDrawer } from "./components/SideDrawer";
import { LocationModal } from "./components/LocationModal";
import { NotificationCenterModal, type NotificationItem } from "./components/NotificationCenterModal";
import { LanguageModal } from "./components/LanguageSelector";
import Navigation from "./components/Navigation";
import AssistanceHub from "./components/AssistanceHub";
import GuidedAssistance from "./components/GuidedAssistance";
import ServicesDirectory from "./components/ServicesDirectory";
import GrievanceWorkflow from "./components/GrievanceWorkflow";
import ChatArea from "./components/ChatArea";
import ChatInput from "./components/ChatInput";
import VoiceModeView from "./components/VoiceModeView";
import { detectUserLocation, type UserLocationData } from "./services/locationService";
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

  // Dedicated Voice Mode Overlay state
  const [isVoiceModeOpen, setIsVoiceModeOpen] = useState(false);

  // Modals and Header UI States
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);
  const [isNotificationModalOpen, setIsNotificationModalOpen] = useState(false);
  const [isLanguageModalOpen, setIsLanguageModalOpen] = useState(false);

  // Location State
  const [locationData, setLocationData] = useState<UserLocationData>({
    status: "idle",
    displayName: "Location unavailable",
    shortDisplayName: "Location",
  });
  const [isDetectingLocation, setIsDetectingLocation] = useState(false);

  // Notifications State (extensible architecture)
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  // Automatically detect location on initial app load
  const handleDetectLocation = useCallback(async () => {
    setIsDetectingLocation(true);
    setLocationData((prev) => ({ ...prev, status: "detecting" }));
    const loc = await detectUserLocation();
    setLocationData(loc);
    setIsDetectingLocation(false);
  }, []);

  useEffect(() => {
    handleDetectLocation();
  }, [handleDetectLocation]);

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
          answer_focus: response.answer_focus,
        });
      } catch (err) {
        console.error("sendQuery error:", err);
        const msg =
          language === "hi"
            ? "सर्वर से संपर्क हो रहा है, कृपया पुनः प्रयास करें।"
            : language === "mr"
            ? "सर्व्हरशी संपर्क होत आहे, कृपया पुन्हा प्रयत्न करा."
            : "Connecting to server… Please try again.";
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    },
    [language, sessionId, addMessage, saveHistoryItem]
  );

  const handleStartGuided = (flowId: string) => {
    setActiveGuidedFlow(flowId);
  };

  const handleGuidedAskAI = (prompt: string) => {
    setActiveGuidedFlow(null);
    handleSendQuery(prompt);
  };

  const handleMarkAllNotificationsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  return (
    <div className="platform-app">
      {/* Top Header Component */}
      <Header
        language={language}
        locationData={locationData}
        unreadNotificationCount={notifications.filter((n) => !n.read).length}
        onOpenMenu={() => setIsDrawerOpen(true)}
        onOpenLocation={() => setIsLocationModalOpen(true)}
        onOpenNotifications={() => setIsNotificationModalOpen(true)}
        onOpenLanguage={() => setIsLanguageModalOpen(true)}
      />

      {/* Hamburger Navigation Drawer */}
      <SideDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        activeTab={activeTab}
        onSelectTab={(tab) => {
          setActiveGuidedFlow(null);
          setIsVoiceModeOpen(false);
          setActiveTab(tab);
        }}
        language={language}
      />

      {/* Location Details Modal */}
      <LocationModal
        isOpen={isLocationModalOpen}
        onClose={() => setIsLocationModalOpen(false)}
        locationData={locationData}
        onRefreshLocation={handleDetectLocation}
        isDetecting={isDetectingLocation}
      />

      {/* Notification Center Modal */}
      <NotificationCenterModal
        isOpen={isNotificationModalOpen}
        onClose={() => setIsNotificationModalOpen(false)}
        notifications={notifications}
        onMarkAllRead={handleMarkAllNotificationsRead}
      />

      {/* 22 Scheduled Languages Selector Modal */}
      <LanguageModal
        isOpen={isLanguageModalOpen}
        onClose={() => setIsLanguageModalOpen(false)}
        selected={language}
        onChange={setLanguage}
      />

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
            onOpenVoiceMode={() => setIsVoiceModeOpen(true)}
            onSelectGuided={handleStartGuided}
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
              onFollowUp={(p) => handleSendQuery(p)}
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

      {/* Dedicated Voice Mode Overlay */}
      {isVoiceModeOpen && (
        <VoiceModeView
          language={language}
          onClose={() => setIsVoiceModeOpen(false)}
          onNavigateToChat={() => setActiveTab("ask")}
        />
      )}

      {/* Single Sticky Input Bar (Shown during Ask Tab or when messages exist) */}
      {(activeTab === "ask" || messages.length > 0) && !isVoiceModeOpen && (
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
          setIsVoiceModeOpen(false);
          setActiveTab(tab);
        }}
        language={language}
      />
    </div>
  );
};

export default App;
