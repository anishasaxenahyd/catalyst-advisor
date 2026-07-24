import type { ReactNode } from "react";
import type { DecisionTrace } from "../types/report";
import { parseEvidence } from "../lib/decisionTrace";
import ScoreBar from "./ScoreBar";
import ConfidenceBadge from "./ConfidenceBadge";
import { IconChevron } from "./icons";

function TraceSection({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: ReactNode;
}) {
  return (
    <details className="trace-section" open={defaultOpen}>
      <summary>
        <IconChevron className="chevron" width={14} height={14} />
        {title}
      </summary>
      <div className="trace-section-body">{children}</div>
    </details>
  );
}

export default function DecisionTraceCard({ trace }: { trace: DecisionTrace }) {
  const { scores, facts } = parseEvidence(trace.evidence);

  return (
    <details className="trace-block">
      <summary>
        <IconChevron className="chevron" width={16} height={16} />
        Decision Trace
      </summary>

      <div className="trace-sections">
        <TraceSection title="Why selected" defaultOpen>
          <p style={{ margin: 0 }}>{trace.why_selected}</p>
        </TraceSection>

        {trace.alternatives_considered.length > 0 && (
          <TraceSection title={`Alternatives considered (${trace.alternatives_considered.length})`}>
            <ul>
              {trace.alternatives_considered.map((alt) => (
                <li key={alt.id}>
                  <strong>{alt.name}</strong> ({Math.round(alt.score)}/100) — {alt.why_lower}
                </li>
              ))}
            </ul>
          </TraceSection>
        )}

        {trace.assumptions.length > 0 && (
          <TraceSection title="Assumptions">
            <ul>
              {trace.assumptions.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </TraceSection>
        )}

        {(scores.length > 0 || facts.length > 0) && (
          <TraceSection title="Evidence">
            {scores.length > 0 && (
              <div className="score-bars">
                {scores.map((s) => (
                  <ScoreBar key={s.dimension} dimension={s.dimension} value={s.value} />
                ))}
              </div>
            )}
            {facts.length > 0 && (
              <ul style={{ marginTop: scores.length > 0 ? "0.75rem" : undefined }}>
                {facts.map((f) => (
                  <li key={f}>
                    <span className="evidence-code">{f}</span>
                  </li>
                ))}
              </ul>
            )}
          </TraceSection>
        )}

        <TraceSection title="Confidence">
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <ConfidenceBadge value={trace.confidence} />
          </div>
        </TraceSection>
      </div>
    </details>
  );
}
