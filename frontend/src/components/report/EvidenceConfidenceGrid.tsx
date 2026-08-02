import type { Report } from "../../types/report";
import ConfidenceBadge from "../ConfidenceBadge";
import { confidenceMeaning } from "../../lib/confidenceLabel";

export default function EvidenceConfidenceGrid({ report }: { report: Report }) {
  const rationale = report.architecture_recommendation.decision_trace.confidence_rationale;

  const rows = [
    {
      key: "overall",
      name: "Overall Solution",
      recommendation: `${report.architecture_recommendation.pattern.name} + ${report.model_recommendation.primary.name}`,
      evidence: rationale,
      confidence: report.confidence_scores.overall,
    },
    {
      key: "architecture",
      name: "Architecture Pattern",
      recommendation: report.architecture_recommendation.pattern.name,
      evidence: report.architecture_recommendation.decision_trace.why_selected,
      confidence: report.confidence_scores.architecture,
    },
    {
      key: "model",
      name: "AI Model",
      recommendation: report.model_recommendation.primary.name,
      evidence: report.model_recommendation.decision_trace.why_selected,
      confidence: report.confidence_scores.model,
    },
    {
      key: "workbench",
      name: "Workbench Configuration",
      recommendation: `${report.workbench_recommendation.workspace_tier.name} / ${report.workbench_recommendation.security_profile.name}`,
      evidence: report.workbench_recommendation.decision_trace.why_selected,
      confidence: report.confidence_scores.workbench,
    },
  ];

  return (
    <div className="rpt-evidence-grid">
      {rows.map((row) => (
        <div className="rpt-evidence-card" key={row.key}>
          <div className="heading">
            <div>
              <p className="kicker">{row.name}</p>
              <p className="name">{row.recommendation}</p>
            </div>
            <ConfidenceBadge value={row.confidence} scheme="confidence" />
          </div>
          <p className="evidence">{row.evidence}</p>
          <p className="meaning">{confidenceMeaning(row.confidence)}</p>
        </div>
      ))}
    </div>
  );
}
