import type { ModelRecommendation } from "../../types/report";
import { relativeBand } from "../../lib/relativeBand";

function levelLabel(level: string): string {
  return level.charAt(0).toUpperCase() + level.slice(1);
}

export default function ModelComparisonTable({ modelRecommendation }: { modelRecommendation: ModelRecommendation }) {
  const { primary, primary_rationale, alternatives, relative_cost, relative_latency } = modelRecommendation;

  const rows = [
    {
      id: primary.id,
      name: primary.name,
      why: primary_rationale,
      strength: primary.strengths[0] ?? "—",
      cost: relative_cost,
      latency: relative_latency,
      bestFor: primary.suitable_for_tags.slice(0, 3).join(", ") || "—",
      recommended: true,
    },
    ...alternatives.map((alt) => ({
      id: alt.model.id,
      name: alt.model.name,
      why: alt.rationale,
      strength: alt.model.strengths[0] ?? "—",
      cost: alt.relative_cost,
      latency: relativeBand(alt.model.latency_tier),
      bestFor: alt.model.suitable_for_tags.slice(0, 3).join(", ") || "—",
      recommended: false,
    })),
  ];

  return (
    <div className="rpt-table-wrap">
      <table className="rpt-table">
        <thead>
          <tr>
            <th>Model</th>
            <th>Why</th>
            <th>Strength</th>
            <th>Cost</th>
            <th>Latency</th>
            <th>Best For</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className={row.recommended ? "recommended" : ""}>
              <td data-label="Model" className="cell-title">
                {row.name}
                {row.recommended && (
                  <span className="rpt-badge accent" style={{ marginLeft: "0.5em" }}>
                    Recommended
                  </span>
                )}
              </td>
              <td data-label="Why">{row.why}</td>
              <td data-label="Strength">{row.strength}</td>
              <td data-label="Cost">{levelLabel(row.cost)}</td>
              <td data-label="Latency">{levelLabel(row.latency)}</td>
              <td data-label="Best For">{row.bestFor}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
