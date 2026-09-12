import React, { useState, useCallback } from "react";
import type { LanguageCode } from "../types";
import { useTranslation } from "../i18n";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";
import {
  WheatIcon,
  LandmarkIcon,
  ScaleIcon,
  WalletCardsIcon,
  FileCheckIcon,
  ClipboardCheckIcon,
  ArrowRightIcon,
  SendIcon,
  MicIcon,
} from "./Icons";

interface Props {
  language: LanguageCode;
  onStartAsk: (initialQuery?: string) => void;
  onOpenVoiceMode: () => void;
  onSelectGuided: (flowType: string) => void;
}

interface ServiceCardConfig {
  id: string;
  icon: React.FC<{ size?: number; color?: string }>;
  titleKey: string;
  descKey: string;
}

const SERVICE_CARDS: ServiceCardConfig[] = [
  {
    id: "crop_damage",
    icon: WheatIcon,
    titleKey: "home.serviceCrop",
    descKey: "home.serviceCropDesc",
  },
  {
    id: "pacs_help",
    icon: LandmarkIcon,
    titleKey: "home.servicePacs",
    descKey: "home.servicePacsDesc",
  },
  {
    id: "coop_rule",
    icon: ScaleIcon,
    titleKey: "home.serviceRules",
    descKey: "home.serviceRulesDesc",
  },
  {
    id: "financial_guidance",
    icon: WalletCardsIcon,
    titleKey: "home.serviceFinance",
    descKey: "home.serviceFinanceDesc",
  },
  {
    id: "schemes_entry",
    icon: FileCheckIcon,
    titleKey: "home.serviceSchemes",
    descKey: "home.serviceSchemesDesc",
  },
  {
    id: "grievance_entry",
    icon: ClipboardCheckIcon,
    titleKey: "home.serviceGrievance",
    descKey: "home.serviceGrievanceDesc",
  },
];

const AssistanceHub: React.FC<Props> = ({
  language,
  onStartAsk,
  onSelectGuided,
}) => {
  const t = useTranslation(language);
  const [typedInput, setTypedInput] = useState("");

  const handleTranscript = useCallback((text: string) => {
    setTypedInput((prev) => (prev ? `${prev} ${text}` : text));
  }, []);

  const { status, errorMessage, startListening, stopListening, clearError, isSupported } =
    useSpeechRecognition({
      language,
      onTranscript: handleTranscript,
    });

  const handleMicClick = () => {
    if (status === "listening") {
      stopListening();
    } else {
      clearError();
      startListening();
    }
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = typedInput.trim();
    if (trimmed) {
      if (status === "listening") {
        stopListening();
      }
      onStartAsk(trimmed);
      setTypedInput("");
    }
  };

  return (
    <div className="assistance-hub" aria-label="SahkaarSetu Assistance Hub">
      {/* Hero Section */}
      <section className="hub-hero">
        <div className="hub-hero__content">
          <h2 className="hub-hero__headline">{t("home.heroHeadline")}</h2>
          <p className="hub-hero__sub">{t("home.heroSub")}</p>

          {/* TEXT QUESTION INPUT WITH VOICE-TO-TEXT MIC BUTTON */}
          <div className="hero-secondary-input">
            <span className="secondary-label">{t("home.typeOr")}</span>

            {/* Listening Status Badge */}
            {status === "listening" && (
              <div className="hero-stt-status hero-stt-status--listening">
                <MicIcon size={14} color="#C53030" />
                <span>{t("home.listeningBadge")}</span>
              </div>
            )}

            <form onSubmit={handleTextSubmit} className="secondary-search-bar">
              <input
                type="text"
                className="secondary-search-input"
                value={typedInput}
                onChange={(e) => {
                  if (errorMessage) clearError();
                  setTypedInput(e.target.value);
                }}
                placeholder={
                  status === "listening"
                    ? t("home.convertingVoice")
                    : t("home.placeholder")
                }
              />

              {/* Speech-to-Text Microphone Button */}
              <button
                type="button"
                className={`secondary-mic-btn ${
                  status === "listening" ? "secondary-mic-btn--active" : ""
                }`}
                onClick={handleMicClick}
                title={
                  !isSupported
                    ? t("home.voiceNotSupported")
                    : status === "listening"
                    ? t("home.clickToStop")
                    : t("home.clickToSpeak")
                }
                aria-label={t("home.clickToSpeak")}
              >
                <MicIcon
                  size={18}
                  color={status === "listening" ? "#C53030" : "#0F6B68"}
                />
              </button>

              {/* Send Button */}
              <button
                type="submit"
                className="secondary-search-btn"
                disabled={!typedInput.trim()}
                aria-label={t("home.submitQuestion")}
              >
                <SendIcon size={16} color="#FFFFFF" />
              </button>
            </form>
          </div>
        </div>
      </section>

      {/* Service Directory Section */}
      <section className="hub-services-section">
        <div className="hub-services-header">
          <h3 className="hub-services__title">{t("home.helpHeader")}</h3>
          <p className="hub-services__sub">{t("home.helpSub")}</p>
        </div>

        <div className="hub-services-grid" role="list">
          {SERVICE_CARDS.map((card) => {
            const IconComp = card.icon;
            const title = t(card.titleKey);
            const desc = t(card.descKey);

            return (
              <button
                key={card.id}
                type="button"
                className="hub-service-card"
                role="listitem"
                onClick={() => onSelectGuided(card.id)}
              >
                <div className="hub-service-card__icon">
                  <IconComp size={20} color="#0F6B68" />
                </div>
                <div className="hub-service-card__body">
                  <span className="hub-service-card__title">{title}</span>
                  <span className="hub-service-card__desc">{desc}</span>
                </div>
                <div className="hub-service-card__arrow">
                  <ArrowRightIcon size={14} color="#68757D" />
                </div>
              </button>
            );
          })}
        </div>
      </section>
    </div>
  );
};

export default AssistanceHub;
