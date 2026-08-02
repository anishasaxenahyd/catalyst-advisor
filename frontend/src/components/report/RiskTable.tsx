import type { Risk } from "../../types/report";

function levelBadgeStyle(level: string): string {
  if (level === "high") return "critical";
  if (level === "medium") return "warning";
  return "good";
}

function levelLabel(level: string): string {
  return level.charAt(0).toUpperCase() + level.slice(1);
}

export default function RiskTable({ risks }: { risks: Risk[] }) {
  return (
    <div className="rpt-table-wrap">
      <table className="rpt-table">
        <thead>
          <tr>
            <th>Risk</th>
            <th>Impact</th>
            <th>Likelihood</th>
            <th>Mitigation</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {risks.map((risk) => (
            <tr key={risk.risk}>
              <td data-label="Risk" className="cell-title">
                {risk.risk}
              </td>
              <td data-label="Impact">
                <span className={`rpt-badge ${levelBadgeStyle(risk.impact)}`}>{levelLabel(risk.impact)}</span>
              </td>
              <td data-label="Likelihood">
                <span className={`rpt-badge ${levelBadgeStyle(risk.likelihood)}`}>{levelLabel(risk.likelihood)}</span>
              </td>
              <td data-label="Mitigation">{risk.mitigation}</td>
              <td data-label="Status">
                <span className="rpt-badge neutral">{risk.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
