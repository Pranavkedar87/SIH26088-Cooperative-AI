import React, { useEffect } from "react";
import { SahkaarSetuLogo } from "./Icons";

interface Props {
  onComplete: () => void;
}

export const SplashScreen: React.FC<Props> = ({ onComplete }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onComplete();
    }, 1900);
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div className="splash-screen-canvas" onClick={onComplete} role="button" tabIndex={0}>
      <div className="splash-center-content">
        <div className="splash-logo-circle">
          <SahkaarSetuLogo size={128} className="splash-logo-img" />
        </div>
        <h1 className="splash-app-title">SahkaarSetu</h1>
        <p className="splash-app-tagline">सहकार से समृद्धि • Cooperation for Prosperity</p>

        {/* Loading Spinner */}
        <div className="splash-spinner-container">
          <div className="splash-spinner-ring" />
        </div>
      </div>
    </div>
  );
};

export default SplashScreen;
