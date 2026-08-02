import type { ScoredApproach } from "../../types/scenario";

const DIMENSIONS: { key: keyof ScoredApproach["scores"]; label: string }[] = [
  { key: "businessFit", label: "Business Fit" },
  { key: "implementationComplexity", label: "Complexity" },
  { key: "security", label: "Security" },
  { key: "compliance", label: "Compliance" },
  { key: "scalability", label: "Scalability" },
  { key: "cost", label: "Cost" },
  { key: "timeToValue", label: "Time-to-Value" },
];

export default function ScoredApproachTable({
  approaches,
  recommendedApproach,
  recommendationRationale,
  investmentEstimate,
}: {
  approaches: ScoredApproach[];
  recommendedApproach: string;
  recommendationRationale: string;
  investmentEstimate: string;
}) {
  return (
    <>
      <p className="approach-caption">
        All dimensions scored 1-10; higher is always more favorable (a high Complexity score means the approach is
        easier to implement, not more complex).
      </p>
      <div className="approach-table-wrap">
        <table className="approach-table">
          <thead>
            <tr>
              <th>Approach</th>
              {DIMENSIONS.map((d) => (
                <th key={d.key}>{d.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {approaches.map((a) => (
              <tr key={a.name} className={a.name === recommendedApproach ? "recommended" : ""}>
                <td className="name-cell" data-label="Approach">
                  {a.name}
                  {a.name === recommendedApproach && <span className="badge-recommended" style={{ marginLeft: "0.6em" }}>Recommended</span>}
                </td>
                {DIMENSIONS.map((d) => (
                  <td key={d.key} className="score" data-label={d.label}>
                    {a.scores[d.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {approaches.map((a) => (
        <div className={`approach-card ${a.name === recommendedApproach ? "recommended" : ""}`} key={a.name}>
          <div className="head">
            <span className="name">{a.name}</span>
          </div>
          <p className="description">{a.description}</p>
          <div className="pros-cons">
            <div>
              <p className="col-label">Pros</p>
              <ul className="plain-list">
                {a.pros.map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="col-label">Cons</p>
              <ul className="plain-list">
                {a.cons.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      ))}

      <div className="recommendation-callout">
        <span className="label">Recommendation</span>
        {recommendationRationale}
        <div className="investment-line">
          <strong>Estimated investment:</strong> {investmentEstimate}
        </div>
      </div>
    </>
  );
}
