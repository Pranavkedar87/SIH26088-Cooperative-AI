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
  const hasSources = !isUser && message.sources && message.sources.length > 0;

  return (
    <div className={`chat-message chat-message--${message.role}`}>
      <div className="chat-message__avatar" aria-hidden="true">
        {isUser ? "👤" : "🤝"}
      </div>
      <div className="chat-message__bubble">
        <p className="chat-message__text">{message.content}</p>
        
        {hasSources && (
          <div className="chat-message__sources">
            <span className="sources-title">📚 Verified Sources:</span>
            <ul className="sources-list">
              {message.sources!.map((s, idx) => (
                <li key={idx} className="source-item">
                  <strong className="source-name">{s.title}</strong>
                  {s.source_name && <span className="source-meta"> — {s.source_name}</span>}
                  {s.source_url && (
                    <a
                      href={s.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="source-link"
                    >
                      🔗 Official Link
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        <span className="chat-message__time">{formatTime(message.timestamp)}</span>
      </div>
    </div>
  );
};

export default ChatMessage;
