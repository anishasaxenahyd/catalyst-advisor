import type { Report } from "../types/report";
import ConfidenceBadge from "./ConfidenceBadge";
import { IconCheckCircle, IconFileWarning } from "./icons";
import { formatDimensionLabel } from "../lib/severity";

/** Surfaces the Phase 2 validation/confidence output that already exists
 * in every Report response but was never rendered until now: how
 * confidence was derived, what fell through to a default, what the
 * validation layer corrected or discarded. Reads from the architecture
 * trace because these three fields are identical across all three
 * DecisionTraces by construction (one signal-vector extraction feeds
 * all of them) — no need to repeat this panel three times. */
export default function RecommendationQualityPanel({ report }: { report: Report }) {
  const trace = report.architecture_recommendation.decision_trace;
  const corrections = report.signal_vector.validation_warnings;

  return (
    <div className="quality-panel">
      <div className="quality-summary-row">
        <span className="confidence-value">{report.confidence_scores.overall}%</span>
        <ConfidenceBadge value={report.confidence_scores.overall} label="overall confidence" />
      </div>
      {trace.confidence_rationale && <p className="quality-rationale">{trace.confidence_rationale}</p>}

      {trace.missing_information.length > 0 && (
        <>
          <h3>Missing information</h3>
          <div className="chip-row">
            {trace.missing_information.map((field) => (
              <span className="chip" key={field}>
                {formatDimensionLabel(field)}
              </span>
            ))}
          </div>
        </>
      )}

      {trace.validation_warnings.length > 0 && (
        <>
          <h3>Validation warnings</h3>
          <ul className="warning-list">
            {trace.validation_warnings.map((warning) => (
              <li className="warning-item" key={warning}>
                <IconFileWarning width={16} height={16} />
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </>
      )}

      {corrections.length > 0 && (
        <>
          <h3>Corrected / discarded values</h3>
          <div style={{ overflowX: "auto" }}>
            <table className="correction-table">
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Original</th>
                  <th>Corrected to</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {corrections.map((warning, idx) => (
                  <tr key={`${warning.field}-${idx}`}>
                    <td>{warning.field}</td>
                    <td>{warning.original_value ? <code>{warning.original_value}</code> : "—"}</td>
                    <td>
                      {warning.corrected_value ? <code>{warning.corrected_value}</code> : "discarded"}
                    </td>
                    <td>{warning.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {trace.missing_information.length === 0 && trace.validation_warnings.length === 0 && (
        <p className="quality-rationale" style={{ display: "flex", alignItems: "center", gap: "0.5em" }}>
          <IconCheckCircle width={16} height={16} style={{ color: "var(--good)" }} />
          No corrections were needed — every signal field was cleanly resolved.
        </p>
      )}
    </div>
  );
}
