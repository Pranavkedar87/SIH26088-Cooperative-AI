import React from "react";
import type { ChatMessage as ChatMessageType } from "../types";

interface Props {
  message: ChatMessageType;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

const ChatMessage: React.FC<Props> = ({ message }) => {
  const isUser = message.role === "user";

  return (
    <div className={`chat-message chat-message--${message.role}`}>
      <div className="chat-message__avatar" aria-hidden="true">
        {isUser ? "👤" : "🤝"}
      </div>
      <div className="chat-message__bubble">
        <p className="chat-message__text">{message.content}</p>
        <span className="chat-message__time">{formatTime(message.timestamp)}</span>
      </div>
    </div>
  );
};

export default ChatMessage;
