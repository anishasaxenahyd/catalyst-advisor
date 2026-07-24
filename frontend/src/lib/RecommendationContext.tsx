import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, requestRecommendation } from "./apiClient";
import type { RecommendationRequest, Report } from "../types/report";

interface RecommendationState {
  status: "idle" | "loading" | "error" | "done";
  report: Report | null;
  error: string | null;
  submit: (request: RecommendationRequest) => void;
  reset: () => void;
}

const RecommendationContext = createContext<RecommendationState | null>(null);

export function RecommendationProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<RecommendationState["status"]>("idle");
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const submit = useCallback(
    (request: RecommendationRequest) => {
      setStatus("loading");
      setError(null);
      navigate("/analyzing");

      requestRecommendation(request)
        .then((result) => {
          setReport(result);
          setStatus("done");
          navigate("/report");
        })
        .catch((err) => {
          const message = err instanceof ApiError ? err.message : "Something went wrong reaching the advisor backend.";
          setError(message);
          setStatus("error");
        });
    },
    [navigate]
  );

  const reset = useCallback(() => {
    setStatus("idle");
    setReport(null);
    setError(null);
    navigate("/");
  }, [navigate]);

  return (
    <RecommendationContext.Provider value={{ status, report, error, submit, reset }}>
      {children}
    </RecommendationContext.Provider>
  );
}

export function useRecommendation(): RecommendationState {
  const ctx = useContext(RecommendationContext);
  if (!ctx) throw new Error("useRecommendation must be used within a RecommendationProvider");
  return ctx;
}
