import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRecommendation } from "../lib/RecommendationContext";
import { IconAlertTriangle, IconCheckCircle, IconLoader, IconRefresh } from "../components/icons";

const STEPS = [
  "Reading your input",
  "Matching against the Catalyst Catalog",
  "Drafting the executive report",
];

export default function Analyzing() {
  const { status, error, reset } = useRecommendation();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (status === "idle") {
      navigate("/");
      return;
    }
    const interval = setInterval(() => {
      setActiveStep((step) => Math.min(step + 1, STEPS.length - 1));
    }, 700);
    return () => clearInterval(interval);
  }, [status, navigate]);

  if (status === "error") {
    return (
      <main className="page">
        <p className="eyebrow">Something went wrong</p>
        <h1>The advisor couldn't finish that request</h1>
        <div className="error-banner">
          <IconAlertTriangle width={18} height={18} />
          <span>{error}</span>
        </div>
        <div className="actions">
          <button className="secondary" onClick={reset}>
            <IconRefresh width={16} height={16} />
            Start over
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="page">
      <p className="eyebrow">
        <IconLoader width={14} height={14} />
        Analyzing
      </p>
      <h1>Building your recommendation</h1>
      <p className="subtitle">
        The deterministic engine is scoring your input against the Catalyst Catalog. This usually takes a
        few seconds.
      </p>
      <div className="steps">
        {STEPS.map((label, idx) => {
          const state = idx < activeStep ? "done" : idx === activeStep ? "active" : "";
          return (
            <div key={label} className={`step ${state}`}>
              {state === "done" ? (
                <IconCheckCircle width={18} height={18} style={{ color: "var(--good)" }} />
              ) : (
                <span className="dot" />
              )}
              {label}
            </div>
          );
        })}
      </div>
    </main>
  );
}
