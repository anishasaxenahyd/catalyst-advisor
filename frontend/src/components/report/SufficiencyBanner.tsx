import { AlertTriangle, HelpCircle } from "lucide-react";
import type { SufficiencyOutcome } from "../../types/report";

// Renders the Sufficiency Gate outcome (Decision Kernel Stage 4) above the
// rest of the report whenever the recommendation is provisional on an
// unanswered, decision-critical question — the design point being that a
// system which always returns a confident architecture is a system that
// will confidently return one when it shouldn't.
export default function SufficiencyBanner({ sufficiency }: { sufficiency: SufficiencyOutcome }) {
  if (sufficiency.status === "PROCEED") return null;

  const isHalt = sufficiency.status === "HALT_CLARIFY";
  const questions = isHalt ? sufficiency.blocking_questions : [...sufficiency.blocking_questions, ...sufficiency.advisory_questions];

  return (
    <div
      className="rpt-card"
      style={{
        borderLeft: `4px solid var(${isHalt ? "--critical" : "--warning"})`,
        background: `var(${isHalt ? "--critical-soft" : "--warning-soft"})`,
        marginBottom: "1.25rem",
        display: "flex",
        gap: "0.75rem",
        alignItems: "flex-start",
      }}
    >
      {isHalt ? (
        <AlertTriangle width={20} height={20} style={{ color: "var(--critical)", flexShrink: 0, marginTop: "0.15rem" }} />
      ) : (
        <HelpCircle width={20} height={20} style={{ color: "var(--warning)", flexShrink: 0, marginTop: "0.15rem" }} />
      )}
      <div>
        <p style={{ fontWeight: 700, margin: "0 0 0.35rem", fontSize: "0.92rem" }}>
          {isHalt ? "This recommendation is provisional — a decision-critical question is unanswered" : "Answer these before treating this as final"}
        </p>
        <p style={{ margin: "0 0 0.5rem", fontSize: "0.86rem", color: "var(--rpt-ink-soft)" }}>{sufficiency.rationale}</p>
        <ul className="rpt-bullet-list">
          {questions.map((q) => (
            <li key={q.field_or_signature}>
              {q.question}
              {q.decision_critical && (
                <span className="rpt-badge critical" style={{ marginLeft: "0.5rem" }}>
                  decision-critical
                </span>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
