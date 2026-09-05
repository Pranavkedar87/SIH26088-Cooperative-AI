import React, { useEffect, useRef, useState } from "react";
import type { ChatMessage as ChatMessageType, LanguageCode } from "../types";
import ChatMessage from "./ChatMessage";

interface Props {
  messages: ChatMessageType[];
  isLoading: boolean;
  language: LanguageCode;
  onSpeak?: (id: string, text: string, language: LanguageCode) => void;
  activeSpeakingId?: string | null;
  onFollowUp?: (prompt: string) => void;
}

// Rotating contextual loading messages
const LOADING_MESSAGES: Record<LanguageCode, string[]> = {
  en: [
    "🔎 Understanding your question…",
    "📚 Checking verified knowledge…",
    "🤖 Preparing your answer…",
    "✅ Almost ready…",
  ],
  hi: [
    "🔎 आपका प्रश्न समझा जा रहा है…",
    "📚 सत्यापित जानकारी खोजी जा रही है…",
    "🤖 आपका उत्तर तैयार हो रहा है…",
    "✅ लगभग तैयार है…",
  ],
  mr: [
    "🔎 तुमचा प्रश्न समजला जात आहे…",
    "📚 सत्यापित ज्ञान तपासले जात आहे…",
    "🤖 तुमचे उत्तर तयार होत आहे…",
    "✅ जवळजवळ तयार आहे…",
  ],
};

const EMPTY_TEXT: Record<LanguageCode, string> = {
  en: "Ask your question below to get started.",
  hi: "शुरू करने के लिए नीचे अपना प्रश्न पूछें।",
  mr: "प्रारंभ करण्यासाठी खाली तुमचा प्रश्न विचारा.",
};

const ChatArea: React.FC<Props> = ({
  messages,
  isLoading,
  language,
  onSpeak,
  activeSpeakingId,
  onFollowUp,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [loadingMsgIdx, setLoadingMsgIdx] = useState(0);

  // Scroll to bottom on new messages / loading state change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Rotate loading message every 1.8 s while loading
  useEffect(() => {
    if (!isLoading) {
      setLoadingMsgIdx(0);
      return;
    }
    setLoadingMsgIdx(0);
    const msgs = LOADING_MESSAGES[language];
    const id = setInterval(() => {
      setLoadingMsgIdx((prev) => (prev + 1) % msgs.length);
    }, 1800);
    return () => clearInterval(id);
  }, [isLoading, language]);

  return (
    <div className="chat-area" role="log" aria-live="polite" aria-label="Conversation">
      {messages.length === 0 && !isLoading && (
        <div className="chat-empty">
          <span className="chat-empty__icon">🤝</span>
          <p>{EMPTY_TEXT[language]}</p>
        </div>
      )}

      {messages.map((msg) => (
        <ChatMessage
          key={msg.id}
          message={msg}
          onSpeak={onSpeak}
          isSpeaking={activeSpeakingId === msg.id}
          onFollowUp={onFollowUp}
        />
      ))}

      {isLoading && (
        <div className="chat-message chat-message--assistant">
          <div className="chat-message__avatar" aria-hidden="true">🤝</div>
          <div className="chat-message__bubble chat-message__bubble--loading">
            <div className="typing-dots" aria-label="Loading">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
            <span className="loading-message-text" key={loadingMsgIdx}>
              {LOADING_MESSAGES[language][loadingMsgIdx]}
            </span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};

export default ChatArea;
