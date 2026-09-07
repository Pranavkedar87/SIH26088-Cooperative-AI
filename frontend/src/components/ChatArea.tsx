import React, { useEffect, useRef, useState } from "react";
import type { ChatMessage as ChatMessageType, LanguageCode } from "../types";
import ChatMessage from "./ChatMessage";
import { MessageSquareIcon } from "./Icons";

interface Props {
  messages: ChatMessageType[];
  isLoading: boolean;
  language: LanguageCode;
  onSpeak?: (id: string, text: string, language: LanguageCode) => void;
  activeSpeakingId?: string | null;
  onFollowUp?: (prompt: string) => void;
  onSimplify?: (prompt: string) => void;
}

// Clean, professional institutional loading messages (No emojis or robotic labels)
const LOADING_MESSAGES: Record<string, string[]> = {
  en: [
    "Consulting verified cooperative & government records…",
    "Synthesizing structured guidance note…",
    "Validating official references, please wait…",
  ],
  hi: [
    "सत्यापित सहकार एवं सरकारी रिकॉर्ड की जांच हो रही है…",
    "आधिकारिक मार्गदर्शन नोट तैयार किया जा रहा है…",
    "सत्यापित संदर्भों की पुष्टि की जा रही है…",
  ],
  mr: [
    "अधिकृत सहकार व शासकीय नोंदींची पडताळणी सुरू आहे…",
    "मार्गदर्शन नोंद तयार केली जात आहे…",
    "संदर्भ माहितीची तपासणी सुरू आहे, कृपया थांबा…",
  ],
};

const EMPTY_TEXT: Record<string, string> = {
  en: "Type your query or select a topic to receive verified cooperative and agricultural guidance.",
  hi: "सत्यापित सहकार एवं कृषि मार्गदर्शन प्राप्त करने के लिए नीचे अपना प्रश्न लिखें।",
  mr: "अधिकृत सहकार व कृषी मार्गदर्शन मिळवण्यासाठी खाली तुमचा प्रश्न विचारा.",
};

export const ChatArea: React.FC<Props> = ({
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

  // Scroll to bottom on new messages / loading state change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Rotate loading message while loading
  useEffect(() => {
    if (!isLoading) {
      setLoadingMsgIdx(0);
      return;
    }
    setLoadingMsgIdx(0);
    const msgs = LOADING_MESSAGES[language] ?? LOADING_MESSAGES.en;
    const id = setInterval(() => {
      setLoadingMsgIdx((prev) => Math.min(prev + 1, msgs.length - 1));
    }, 5000);
    return () => clearInterval(id);
  }, [isLoading, language]);

  return (
    <div className="chat-area" role="log" aria-live="polite" aria-label="Guidance Conversation Transcript">
      {messages.length === 0 && !isLoading && (
        <div className="chat-empty">
          <div className="chat-empty__icon-box">
            <MessageSquareIcon size={24} color="#0F6B68" />
          </div>
          <p className="chat-empty__text">{EMPTY_TEXT[language] ?? EMPTY_TEXT.en}</p>
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
        <div className="chat-row chat-row--assistant">
          <div className="chat-card chat-card--loading" role="status" aria-label="Loading response">
            <div className="typing-dots" aria-hidden="true">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
            <span className="loading-message-text" key={loadingMsgIdx}>
              {(LOADING_MESSAGES[language] ?? LOADING_MESSAGES.en)[loadingMsgIdx]}
            </span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};

export default ChatArea;
