import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useRecommendation } from "../lib/RecommendationContext";
import DecisionTraceCard from "../components/DecisionTraceCard";
import SolutionBlueprint from "../components/SolutionBlueprint";
import ConfidenceBadge from "../components/ConfidenceBadge";
import StatTile from "../components/StatTile";
import RecommendationQualityPanel from "../components/RecommendationQualityPanel";
import { formatAssetCategory } from "../lib/catalogLabels";
import {
  IconAlertTriangle,
  IconArrowRight,
  IconCheckCircle,
  IconClock,
  IconCloud,
  IconDiagram,
  IconEye,
  IconFileText,
  IconInfo,
  IconLayers,
  IconLightbulb,
  IconPrint,
  IconRefresh,
  IconRoute,
  IconServer,
  IconShield,
  IconSparkles,
  IconTarget,
} from "../components/icons";

const NAV_SECTIONS = [
  { id: "overview", label: "Overview" },
  { id: "architecture", label: "Architecture" },
  { id: "components", label: "Components" },
  { id: "evidence", label: "Evidence & Confidence" },
  { id: "enterprise-fit", label: "Enterprise Fit" },
  { id: "security", label: "Security & Governance" },
  { id: "roadmap", label: "Roadmap" },
];

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

  const { signal_vector, architecture_recommendation, model_recommendation, workbench_recommendation, enrichment } =
    report;
  const modeLabel = report.mode === "idea" ? "Idea mode" : "Design review";
  const hasEnrichment = Boolean(enrichment);

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

      <nav className="report-subnav" aria-label="Report sections">
        {NAV_SECTIONS.filter((s) => hasEnrichment || !["enterprise-fit", "security"].includes(s.id)).map((s) => (
          <a key={s.id} href={`#${s.id}`}>
            {s.label}
          </a>
        ))}
      </nav>

      {/* ================================================================ */}
      {/* 01 — Executive Overview                                          */}
      {/* ================================================================ */}
      <div className="section-group" id="overview">
        <div className="section-group-head">
          <p className="eyebrow">Section 01</p>
          <h2>Executive overview</h2>
          <p>What was asked, what we understood, and the recommendation at a glance.</p>
        </div>

        <section className="exec-summary">
          <p className="lede">{report.executive_summary}</p>
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
            <div className="primary-tile">
              <div className="label">Overall confidence</div>
              <div className="value">{report.confidence_scores.overall}%</div>
              <div className="detail">
                Effort {report.effort_estimate} · timeline {report.timeline_estimate}
              </div>
            </div>
          </div>
        </section>

        {enrichment && (
          <section className="section" style={{ marginBottom: 0 }}>
            <div className="section-head">
              <h2>
                <IconInfo width={18} height={18} className="icon" />
                Business understanding
              </h2>
            </div>
            <div className="card">
              <p className="description">{enrichment.business_understanding.problem_narrative}</p>
              <div className="chip-row">
                <span className="chip">Use case: {enrichment.business_understanding.use_case_type}</span>
                <span className="chip">Industry: {enrichment.business_understanding.industry}</span>
                <span className="chip">Data sensitivity: {enrichment.business_understanding.data_sensitivity}</span>
                <span className="chip">Scale: {enrichment.business_understanding.expected_scale}</span>
                <span className="chip">Automation: {enrichment.business_understanding.automation_level}</span>
              </div>
              <ul className="plain-list" style={{ marginTop: "0.75rem" }}>
                {enrichment.business_understanding.key_signals.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          </section>
        )}
      </div>

      {/* ================================================================ */}
      {/* 02 — Recommended Architecture                                    */}
      {/* ================================================================ */}
      <div className="section-group" id="architecture">
        <div className="section-group-head">
          <p className="eyebrow">Section 02</p>
          <h2>Recommended architecture</h2>
          <p>The solution architecture, why this pattern was selected, and what else was considered.</p>
        </div>

        <section className="section">
          <div className="section-head">
            <h2>
              <IconDiagram width={18} height={18} className="icon" />
              Enterprise solution blueprint
            </h2>
          </div>
          <p className="subtitle" style={{ marginBottom: "1rem" }}>
            If you were building this tomorrow, here's what the architecture would look like — assembled from
            the specific components recommended below, not a generic AI pattern. Click any component for
            details, or switch views to see security, AI-catalog, or data-flow emphasis.
          </p>
          <SolutionBlueprint report={report} />
        </section>

        <section className="section" style={{ marginBottom: 0 }}>
          <div className="section-head">
            <h2>
              <IconTarget width={18} height={18} className="icon" />
              Architecture pattern
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
            <div className="rationale-callout">
              <span className="callout-label">Why this architecture</span>
              {architecture_recommendation.rationale}
            </div>
            <DecisionTraceCard trace={architecture_recommendation.decision_trace} />
          </div>

          {architecture_recommendation.decision_trace.alternatives_considered.length > 0 && (
            <>
              <h3 className="subhead spaced">Alternatives considered</h3>
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
      </div>

      {/* ================================================================ */}
      {/* 03 — Solution Components                                         */}
      {/* ================================================================ */}
      <div className="section-group" id="components">
        <div className="section-group-head">
          <p className="eyebrow">Section 03</p>
          <h2>Solution components</h2>
          <p>The AI model, workflow components, and Workbench configuration that make up this recommendation.</p>
        </div>

        <section className="section">
          <div className="section-head">
            <h2>
              <IconLayers width={18} height={18} className="icon" />
              Recommended workflow components
            </h2>
          </div>
          <ul className="asset-list">
            {report.enterprise_reuse.map((item) => (
              <li key={item.asset.id}>
                <div className="name">
                  {item.asset.name} <span className="chip">{formatAssetCategory(item.asset.category)}</span>
                </div>
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
            <div className="rationale-callout">
              <span className="callout-label">Why this model</span>
              {model_recommendation.primary_rationale}
            </div>
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
              <h3 className="subhead spaced">Alternative models</h3>
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

        <section className="section" style={{ marginBottom: 0 }}>
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
      </div>

      {/* ================================================================ */}
      {/* 04 — Evidence & Confidence                                       */}
      {/* ================================================================ */}
      <div className="section-group" id="evidence">
        <div className="section-group-head">
          <p className="eyebrow">Section 04</p>
          <h2>Evidence &amp; confidence</h2>
          <p>How much to trust this recommendation, and what it's grounded in.</p>
        </div>

        <section className="section" style={{ marginBottom: 0 }}>
          <div className="section-head">
            <h2>
              <IconEye width={18} height={18} className="icon" />
              Recommendation quality
            </h2>
          </div>
          <div className="stat-grid" style={{ marginBottom: "1rem" }}>
            <StatTile label="Overall" value={`${report.confidence_scores.overall}%`} />
            <StatTile label="Architecture" value={`${report.confidence_scores.architecture}%`} />
            <StatTile label="Model" value={`${report.confidence_scores.model}%`} />
            <StatTile label="Workbench" value={`${report.confidence_scores.workbench}%`} />
          </div>
          {enrichment && (
            <div className="stat-grid" style={{ marginBottom: "1rem" }}>
              <StatTile
                label="Best practices referenced"
                value={enrichment.evidence_confidence_summary.best_practice_count}
              />
              <StatTile
                label="Comparable implementations"
                value={enrichment.evidence_confidence_summary.similar_solution_count}
              />
              <StatTile
                label="Reusable assets matched"
                value={enrichment.evidence_confidence_summary.reusable_asset_count}
              />
            </div>
          )}
          <RecommendationQualityPanel report={report} />
        </section>
      </div>

      {/* ================================================================ */}
      {/* 05 — Enterprise Fit & Precedent                                  */}
      {/* ================================================================ */}
      {enrichment && (
        <div className="section-group" id="enterprise-fit">
          <div className="section-group-head">
            <p className="eyebrow">Section 05</p>
            <h2>Enterprise fit &amp; precedent</h2>
            <p>Reusable assets, comparable implementations, and industry guidance behind this recommendation.</p>
          </div>

          <section className="section" style={{ marginBottom: 0 }}>
            <div className="section-head">
              <h2>
                <IconLightbulb width={18} height={18} className="icon" />
                Enterprise context
              </h2>
            </div>

            {enrichment.reusable_assets.length > 0 && (
              <>
                <h3 className="subhead">Reusable AI Catalog assets</h3>
                <ul className="asset-list">
                  {enrichment.reusable_assets.map((asset) => (
                    <li key={asset.id}>
                      <div className="name">
                        {asset.name} <span className="chip">{asset.asset_type.replace(/_/g, " ")}</span>
                      </div>
                      <p className="rationale">{asset.rationale}</p>
                    </li>
                  ))}
                </ul>
              </>
            )}

            {enrichment.similar_solutions.length > 0 && (
              <>
                <h3 className="subhead spaced">
                  <IconRoute width={14} height={14} className="icon" /> Similar enterprise solutions
                </h3>
                <div className="comparison-grid">
                  {enrichment.similar_solutions.map((sol) => (
                    <div className="comparison-card" key={sol.id}>
                      <span className="name">
                        {sol.title} <span className="chip">{sol.industry}</span>
                      </span>
                      <span className="rationale" style={{ fontSize: "0.85rem" }}>
                        {sol.business_outcome}
                      </span>
                      {sol.lessons_learned.length > 0 && (
                        <span className="why-lower">Lesson learned: {sol.lessons_learned[0]}</span>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}

            {enrichment.best_practices.length > 0 && (
              <>
                <h3 className="subhead spaced">
                  <IconFileText width={14} height={14} className="icon" /> Industry best practices consulted
                </h3>
                <div className="card">
                  <ul className="plain-list">
                    {enrichment.best_practices.map((bp) => (
                      <li key={bp.id}>
                        <strong>{bp.title}</strong> — {bp.summary}
                        <span className="chip-row" style={{ marginTop: "0.35rem", display: "inline-flex" }}>
                          <span className="chip">{bp.vendor.replace(/_/g, " ")}</span>
                          <span className="chip">{bp.reference}</span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            )}
          </section>
        </div>
      )}

      {/* ================================================================ */}
      {/* 06 — Security & Governance                                       */}
      {/* ================================================================ */}
      {enrichment && (
        <div className="section-group" id="security">
          <div className="section-group-head">
            <p className="eyebrow">Section 06</p>
            <h2>Security &amp; governance</h2>
            <p>Controls, compliance posture, and governance guardrails this recommendation assumes.</p>
          </div>

          <section className="section" style={{ marginBottom: 0 }}>
            <div className="section-head">
              <h2>
                <IconShield width={18} height={18} className="icon" />
                Security considerations
              </h2>
            </div>
            <div className="card">
              <div className="chip-row">
                <span className="chip">{enrichment.security_summary.security_profile_name} profile</span>
                {enrichment.security_summary.compliance_flags.map((f) => (
                  <span className="chip" key={f}>
                    {f}
                  </span>
                ))}
              </div>
              <ul className="plain-list" style={{ marginTop: "0.5rem" }}>
                {enrichment.security_summary.considerations.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
              {enrichment.security_summary.relevant_controls.length > 0 && (
                <>
                  <h3 className="subhead spaced">Relevant controls (Enterprise Knowledge Platform)</h3>
                  <ul className="plain-list">
                    {enrichment.security_summary.relevant_controls.map((c) => (
                      <li key={c.id}>
                        <strong>{c.title}</strong> — {c.summary}
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>

            {enrichment.governance_recommendations.length > 0 && (
              <>
                <h3 className="subhead spaced">
                  <IconAlertTriangle width={14} height={14} className="icon" /> Governance recommendations
                </h3>
                <div className="comparison-grid">
                  {enrichment.governance_recommendations.map((g) => (
                    <div className="comparison-card" key={g.title}>
                      <span className="name">
                        {g.title}
                        {g.framework && <span className="chip">{g.framework}</span>}
                      </span>
                      <span className="rationale" style={{ fontSize: "0.85rem" }}>
                        {g.rationale}
                      </span>
                      <span className="why-lower">
                        Source: {g.source === "enterprise_knowledge" ? "Enterprise Knowledge Platform" : "policy rule"}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </section>
        </div>
      )}

      {/* ================================================================ */}
      {/* 07 — Roadmap & Next Steps                                        */}
      {/* ================================================================ */}
      <div className="section-group" id="roadmap">
        <div className="section-group-head">
          <p className="eyebrow">Section 07</p>
          <h2>Roadmap &amp; next steps</h2>
          <p>A phased path to production, key risks, and what to do next.</p>
        </div>

        {enrichment && enrichment.implementation_roadmap.phases.length > 0 && (
          <section className="section">
            <div className="section-head">
              <h2>
                <IconClock width={18} height={18} className="icon" />
                Implementation roadmap
              </h2>
            </div>
            <p className="subtitle" style={{ marginBottom: "1rem" }}>
              Total estimated timeline: {enrichment.implementation_roadmap.total_timeline}
            </p>
            <div className="roadmap-timeline">
              {enrichment.implementation_roadmap.phases.map((phase, idx) => (
                <div className="roadmap-step" key={phase.name}>
                  <div className="marker-col">
                    <div className="marker">{idx + 1}</div>
                    <div className="connector" />
                  </div>
                  <div className="step-body">
                    <div className="step-head">
                      <h3>{phase.name}</h3>
                      <span className="chip">{phase.duration}</span>
                    </div>
                    <div className="roadmap-columns">
                      <div>
                        <h4>Goals</h4>
                        <ul className="plain-list">
                          {phase.goals.map((goal) => (
                            <li key={goal}>{goal}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h4>Deliverables</h4>
                        <ul className="plain-list">
                          {phase.deliverables.map((d) => (
                            <li key={d}>{d}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="section" style={{ marginBottom: 0 }}>
          <div className="section-head">
            <h2>
              <IconArrowRight width={18} height={18} className="icon" />
              Path forward
            </h2>
          </div>
          <div className="two-col">
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
            <div className="card">
              <h3 style={{ fontSize: "0.9rem", marginBottom: "0.5rem" }}>Next best actions</h3>
              <ul className="plain-list">
                {report.next_best_actions.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
