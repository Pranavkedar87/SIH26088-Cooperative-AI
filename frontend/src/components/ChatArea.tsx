import React, { useEffect, useRef } from "react";
import type { ChatMessage as ChatMessageType, LanguageCode } from "../types";
import ChatMessage from "./ChatMessage";

interface Props {
  messages: ChatMessageType[];
  isLoading: boolean;
  language: LanguageCode;
  onSpeak?: (id: string, text: string, language: LanguageCode) => void;
  activeSpeakingId?: string | null;
}

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
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

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
        />
      ))}

      {isLoading && (
        <div className="chat-message chat-message--assistant">
          <div className="chat-message__avatar" aria-hidden="true">🤝</div>
          <div className="chat-message__bubble chat-message__bubble--loading">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};

export default ChatArea;
