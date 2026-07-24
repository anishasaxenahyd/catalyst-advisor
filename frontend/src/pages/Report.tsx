import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useRecommendation } from "../lib/RecommendationContext";
import DecisionTraceCard from "../components/DecisionTraceCard";
import MermaidDiagram from "../components/MermaidDiagram";
import ConfidenceBadge from "../components/ConfidenceBadge";
import StatTile from "../components/StatTile";
import RecommendationQualityPanel from "../components/RecommendationQualityPanel";
import {
  IconArrowRight,
  IconBarChart,
  IconCheckCircle,
  IconCloud,
  IconDiagram,
  IconLayers,
  IconPrint,
  IconRefresh,
  IconServer,
  IconShield,
  IconSparkles,
  IconTarget,
} from "../components/icons";

export default function ReportPage() {
  const { status, report, reset } = useRecommendation();
  const navigate = useNavigate();

  useEffect(() => {
    if (status !== "done" || !report) {
      navigate("/");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  if (!report) {
    return (
      <main className="page">
        <div className="empty-state">
          <IconDiagram width={40} height={40} className="icon" />
          <p>No report to show yet — start from an idea or an architecture upload.</p>
          <button className="primary" onClick={() => navigate("/")}>
            Go to landing
          </button>
        </div>
      </main>
    );
  }

  const { signal_vector, architecture_recommendation, model_recommendation, workbench_recommendation } = report;
  const modeLabel = report.mode === "idea" ? "Idea mode" : "Design review";

  return (
    <main className="page wide">
      <div className="report-header">
        <div>
          <p className="eyebrow">
            <IconSparkles width={14} height={14} />
            Executive Report
          </p>
          <h1>{signal_vector.use_case_type}</h1>
          <div className="report-meta">
            <span className="badge neutral">{modeLabel}</span>
            <ConfidenceBadge value={report.confidence_scores.overall} />
            <span className="badge neutral">{signal_vector.industry}</span>
          </div>
        </div>
        <div className="actions" style={{ marginTop: 0 }}>
          <button className="secondary" onClick={() => window.print()}>
            <IconPrint width={16} height={16} />
            Export / Print
          </button>
          <button className="secondary" onClick={reset}>
            <IconRefresh width={16} height={16} />
            Start over
          </button>
        </div>
      </div>

      <section className="exec-summary">
        <p>{report.executive_summary}</p>
      </section>

      <div className="primary-strip">
        <div className="primary-tile">
          <div className="label">Architecture pattern</div>
          <div className="value">{architecture_recommendation.pattern.name}</div>
          <div className="detail">Complexity tier {architecture_recommendation.pattern.complexity_tier}/5</div>
        </div>
        <div className="primary-tile">
          <div className="label">Primary model</div>
          <div className="value">{model_recommendation.primary.name}</div>
          <div className="detail">
            Relative cost {model_recommendation.relative_cost} · latency {model_recommendation.relative_latency}
          </div>
        </div>
        <div className="primary-tile">
          <div className="label">Workbench</div>
          <div className="value">{workbench_recommendation.workspace_tier.name}</div>
          <div className="detail">{workbench_recommendation.security_profile.name} security profile</div>
        </div>
      </div>

      <div className="stat-grid section">
        <StatTile label="Technical feasibility" value={`${report.feasibility.technical}/100`} />
        <StatTile label="Business feasibility" value={`${report.feasibility.business}/100`} />
        <StatTile label="Effort estimate" value={report.effort_estimate} />
        <StatTile label="Timeline" value={report.timeline_estimate} />
      </div>

      <section className="section">
        <div className="section-head">
          <h2>
            <IconBarChart width={18} height={18} className="icon" />
            Recommendation quality
          </h2>
        </div>
        <RecommendationQualityPanel report={report} />
      </section>

      <section className="section">
        <div className="section-head">
          <h2>
            <IconTarget width={18} height={18} className="icon" />
            Recommended architecture pattern
          </h2>
        </div>
        <div className="card selected">
          <div className="card-head">
            <h3>{architecture_recommendation.pattern.name}</h3>
            <span className="badge good">
              <IconCheckCircle width={14} height={14} strokeWidth={2} />
              Selected
            </span>
          </div>
          <p className="description">{architecture_recommendation.pattern.description}</p>
          <p className="rationale">{architecture_recommendation.rationale}</p>
          <MermaidDiagram source={architecture_recommendation.pattern.mermaid_template} />
          <DecisionTraceCard trace={architecture_recommendation.decision_trace} />
        </div>

        {architecture_recommendation.decision_trace.alternatives_considered.length > 0 && (
          <>
            <h3 style={{ fontSize: "0.85rem", color: "var(--ink-muted)", margin: "1.25rem 0 0.75rem" }}>
              Alternatives considered
            </h3>
            <div className="comparison-grid">
              {architecture_recommendation.decision_trace.alternatives_considered.map((alt) => (
                <div className="comparison-card" key={alt.id}>
                  <span className="name">{alt.name}</span>
                  <span className="score-line">{Math.round(alt.score)}/100</span>
                  <span className="why-lower">{alt.why_lower}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </section>

      <section className="section">
        <div className="section-head">
          <h2>
            <IconLayers width={18} height={18} className="icon" />
            Enterprise asset reuse
          </h2>
        </div>
        <ul className="asset-list">
          {report.enterprise_reuse.map((item) => (
            <li key={item.asset.id}>
              <div className="name">
                {item.asset.name} <span className="chip">{item.asset.category.replace("_", " ")}</span>
              </div>
              <div className="rationale">{item.rationale}</div>
            </li>
          ))}
        </ul>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>
            <IconSparkles width={18} height={18} className="icon" />
            Recommended AI model
          </h2>
        </div>
        <div className="card selected">
          <div className="card-head">
            <h3>{model_recommendation.primary.name}</h3>
            <span className="badge good">
              <IconCheckCircle width={14} height={14} strokeWidth={2} />
              Primary
            </span>
          </div>
          <p className="rationale">{model_recommendation.primary_rationale}</p>
          <p className="rationale">{model_recommendation.suitability_rationale}</p>
          <div className="chip-row">
            <span className="chip">Relative cost: {model_recommendation.relative_cost}</span>
            <span className="chip">Relative latency: {model_recommendation.relative_latency}</span>
            {model_recommendation.primary.compliance.map((c) => (
              <span className="chip" key={c}>
                {c}
              </span>
            ))}
          </div>
          <DecisionTraceCard trace={model_recommendation.decision_trace} />
        </div>

        {model_recommendation.alternatives.length > 0 && (
          <>
            <h3 style={{ fontSize: "0.85rem", color: "var(--ink-muted)", margin: "1.25rem 0 0.75rem" }}>
              Alternative models
            </h3>
            <div className="comparison-grid">
              {model_recommendation.alternatives.map((alt) => (
                <div className="comparison-card" key={alt.model.id}>
                  <span className="name">{alt.model.name}</span>
                  <span className="rationale" style={{ fontSize: "0.85rem" }}>
                    {alt.rationale}
                  </span>
                  <span className="why-lower">Trade-off: {alt.trade_off}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </section>

      <section className="section">
        <div className="section-head">
          <h2>
            <IconServer width={18} height={18} className="icon" />
            Recommended AI Workbench configuration
          </h2>
        </div>
        <div className="workbench-grid">
          <div className="workbench-card">
            <IconLayers width={18} height={18} className="icon" />
            <div className="label">Workspace tier</div>
            <div className="value">{workbench_recommendation.workspace_tier.name}</div>
            <p className="reason">{workbench_recommendation.reasons.workspace}</p>
          </div>
          <div className="workbench-card">
            <IconServer width={18} height={18} className="icon" />
            <div className="label">Compute profile</div>
            <div className="value">{workbench_recommendation.compute_profile.name}</div>
            <p className="reason">{workbench_recommendation.reasons.compute}</p>
          </div>
          <div className="workbench-card">
            <IconShield width={18} height={18} className="icon" />
            <div className="label">Security profile</div>
            <div className="value">{workbench_recommendation.security_profile.name}</div>
            <p className="reason">{workbench_recommendation.reasons.security}</p>
          </div>
          <div className="workbench-card">
            <IconCloud width={18} height={18} className="icon" />
            <div className="label">Deployment targets</div>
            <div className="value">{workbench_recommendation.deployment_targets.map((t) => t.name).join(", ")}</div>
            <p className="reason">{workbench_recommendation.reasons.deployment}</p>
          </div>
        </div>
        <DecisionTraceCard trace={workbench_recommendation.decision_trace} />
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Risks &amp; assumptions</h2>
        </div>
        <div className="card">
          <h3 style={{ fontSize: "0.9rem", marginBottom: "0.5rem" }}>Risks</h3>
          <ul className="plain-list">
            {report.risks.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
          <h3 style={{ fontSize: "0.9rem", margin: "1rem 0 0.5rem" }}>Assumptions</h3>
          <ul className="plain-list">
            {report.assumptions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Confidence scores</h2>
        </div>
        <div className="stat-grid">
          <StatTile label="Overall" value={`${report.confidence_scores.overall}%`} />
          <StatTile label="Architecture" value={`${report.confidence_scores.architecture}%`} />
          <StatTile label="Model" value={`${report.confidence_scores.model}%`} />
          <StatTile label="Workbench" value={`${report.confidence_scores.workbench}%`} />
        </div>
      </section>

      <section className="section" style={{ marginBottom: 0 }}>
        <div className="section-head">
          <h2>
            <IconArrowRight width={18} height={18} className="icon" />
            Next best actions
          </h2>
        </div>
        <div className="card">
          <ul className="plain-list">
            {report.next_best_actions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </div>
      </section>
    </main>
  );
}
