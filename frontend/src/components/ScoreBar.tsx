import { formatDimensionLabel, severityFor, SEVERITY_COLOR_VAR } from "../lib/severity";

export default function ScoreBar({ dimension, value }: { dimension: string; value: number }) {
  const clamped = Math.max(0, Math.min(100, value));
  const color = SEVERITY_COLOR_VAR[severityFor(clamped)];

  return (
    <div className="score-bar-row">
      <span className="dim-label">{formatDimensionLabel(dimension)}</span>
      <div
        className="score-bar-track"
        role="meter"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={formatDimensionLabel(dimension)}
      >
        <div className="score-bar-fill" style={{ width: `${clamped}%`, background: color }} />
      </div>
      <span className="score-bar-value">{Math.round(clamped)}</span>
    </div>
  );
}
