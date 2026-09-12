import React, { useEffect, useRef, useState } from "react";
import type { ChatMessage as ChatMessageType, LanguageCode } from "../types";
import { useTranslation } from "../i18n";
import ChatMessage from "./ChatMessage";

interface Props {
  messages: ChatMessageType[];
  isLoading: boolean;
  language: LanguageCode;
  onSpeak?: (id: string, text: string, language: LanguageCode) => void;
  activeSpeakingId?: string | null;
  onFollowUp?: (prompt: string) => void;
  onSimplify?: (prompt: string) => void;
}

const ChatArea: React.FC<Props> = ({
  messages,
  isLoading,
  language,
  onSpeak,
  activeSpeakingId,
  onFollowUp,
  onSimplify,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [loadingMsgIdx, setLoadingMsgIdx] = useState(0);
  const t = useTranslation(language);

  const loadingMessages = [
    t("chat.loading1"),
    t("chat.loading2"),
    t("chat.loading3"),
    t("chat.loading4"),
  ];

  // Scroll to bottom on new messages / loading state change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Rotate loading message every 6s while loading
  useEffect(() => {
    if (!isLoading) {
      setLoadingMsgIdx(0);
      return;
    }
    setLoadingMsgIdx(0);
    const id = setInterval(() => {
      setLoadingMsgIdx((prev) => Math.min(prev + 1, loadingMessages.length - 1));
    }, 6000);
    return () => clearInterval(id);
  }, [isLoading, loadingMessages.length]);

  return (
    <div className="chat-area" role="log" aria-live="polite" aria-label="Conversation">
      {messages.length === 0 && !isLoading && (
        <div className="chat-empty">
          <span className="chat-empty__icon">🤝</span>
          <p>{t("chat.emptyState")}</p>
        </div>
      )}

      {messages.map((msg, index) => {
        const userQuestion =
          msg.role === "assistant" && index > 0 && messages[index - 1].role === "user"
            ? messages[index - 1].content
            : undefined;

        return (
          <ChatMessage
            key={msg.id}
            message={msg}
            userQuestion={userQuestion}
            onSpeak={onSpeak}
            isSpeaking={activeSpeakingId === msg.id}
            onFollowUp={onFollowUp}
            onSimplify={onSimplify}
          />
        );
      })}

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
              {loadingMessages[loadingMsgIdx]}
            </span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};

export default ChatArea;
