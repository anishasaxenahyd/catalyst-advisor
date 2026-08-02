import type { Report } from "../types/report";
import ConfidenceBadge from "./ConfidenceBadge";
import { CheckCircle2, FileWarning } from "lucide-react";
import { formatDimensionLabel } from "../lib/severity";

/** Surfaces the validation/confidence output that already exists in every
 * Report response: how confidence was derived, what fell through to a
 * default, what the validation layer corrected or discarded. Reads from
 * the architecture trace because these three fields are identical across
 * all three DecisionTraces by construction (one signal-vector extraction
 * feeds all of them) — no need to repeat this panel three times. */
export default function RecommendationQualityPanel({ report }: { report: Report }) {
  const trace = report.architecture_recommendation.decision_trace;
  const corrections = report.signal_vector.validation_warnings;

  return (
    <div className="rpt-card rpt-quality-panel">
      <div className="rpt-quality-summary-row">
        <span className="rpt-confidence-value">{report.confidence_scores.overall}%</span>
        <ConfidenceBadge value={report.confidence_scores.overall} scheme="confidence" label="overall confidence" />
      </div>
      {trace.confidence_rationale && <p className="rpt-quality-rationale">{trace.confidence_rationale}</p>}

      {trace.missing_information.length > 0 && (
        <>
          <h3>Missing information</h3>
          <div className="rpt-chip-row">
            {trace.missing_information.map((field) => (
              <span className="rpt-chip" key={field}>
                {formatDimensionLabel(field)}
              </span>
            ))}
          </div>
        </>
      )}

      {trace.validation_warnings.length > 0 && (
        <>
          <h3>Validation warnings</h3>
          <ul className="rpt-warning-list">
            {trace.validation_warnings.map((warning) => (
              <li className="rpt-warning-item" key={warning}>
                <FileWarning width={16} height={16} />
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </>
      )}

      {corrections.length > 0 && (
        <>
          <h3>Corrected / discarded values</h3>
          <div className="rpt-table-wrap">
            <table className="rpt-table">
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
                    <td data-label="Field">{warning.field}</td>
                    <td data-label="Original">{warning.original_value ? <code>{warning.original_value}</code> : "—"}</td>
                    <td data-label="Corrected to">
                      {warning.corrected_value ? <code>{warning.corrected_value}</code> : "discarded"}
                    </td>
                    <td data-label="Reason">{warning.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {trace.missing_information.length === 0 && trace.validation_warnings.length === 0 && (
        <p className="rpt-quality-rationale" style={{ display: "flex", alignItems: "center", gap: "0.5em" }}>
          <CheckCircle2 width={16} height={16} style={{ color: "var(--good)" }} />
          No corrections were needed — every signal field was cleanly resolved.
        </p>
      )}
    </div>
  );
}
