import React from "react";
import { AlertTriangleIcon } from "../Icons";

interface Props {
  warnings: string[];
  language?: string;
}

export const WarningCard: React.FC<Props> = ({ warnings, language = "mr" }) => {
  if (!warnings || warnings.length === 0) return null;

  const headerTitle =
    language === "hi"
      ? "महत्वपूर्ण सूचना"
      : language === "en"
      ? "Important Notice"
      : "महत्त्वाचे / मुदत";

  return (
    <div className="guidance-warning-card">
      <div className="guidance-warning-card__header">
        <AlertTriangleIcon size={16} color="#B7791F" />
        <span className="guidance-warning-card__title">{headerTitle}</span>
      </div>
      <div className="guidance-warning-card__body">
        {warnings.map((warn, i) => (
          <p key={i} className="guidance-warning-card__text">
            {warn}
          </p>
        ))}
      </div>
    </div>
  );
};

export default WarningCard;
