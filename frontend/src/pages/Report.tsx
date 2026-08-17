import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  CalendarClock,
  CheckCircle2,
  Cpu,
  Eye,
  Library,
  ListChecks,
  Network,
  Puzzle,
  Scale,
  Settings2,
  ShieldAlert,
  Target,
  TrendingUp,
  Workflow,
} from "lucide-react";
import { useRecommendation } from "../lib/RecommendationContext";
import DecisionTraceCard from "../components/DecisionTraceCard";
import SolutionBlueprint from "../components/SolutionBlueprint";
import RecommendationQualityPanel from "../components/RecommendationQualityPanel";
import ReportHeader from "../components/report/ReportHeader";
import ExecutiveCardsGrid from "../components/report/ExecutiveCardsGrid";
import SolutionComponentCard from "../components/report/SolutionComponentCard";
import ModelComparisonTable from "../components/report/ModelComparisonTable";
import WorkbenchGroup from "../components/report/WorkbenchGroup";
import EvidenceConfidenceGrid from "../components/report/EvidenceConfidenceGrid";
import AlternativeSolutionCard from "../components/report/AlternativeSolutionCard";
import RoadmapTimeline from "../components/report/RoadmapTimeline";
import RiskTable from "../components/report/RiskTable";
import BusinessValueKpis from "../components/report/BusinessValueKpis";
import SufficiencyBanner from "../components/report/SufficiencyBanner";
import DecisionKernelPanel from "../components/report/DecisionKernelPanel";
import { IconDiagram } from "../components/icons";
import "../report.css";

const NAV_SECTIONS = [
  { id: "overview", label: "Overview" },
  { id: "architecture", label: "Architecture" },
  { id: "decision-kernel", label: "How We Decided" },
  { id: "components", label: "Components" },
  { id: "models", label: "AI Models" },
  { id: "workbench", label: "Workbench" },
  { id: "evidence", label: "Evidence & Confidence" },
  { id: "alternatives", label: "Alternatives" },
  { id: "precedent", label: "Enterprise Fit" },
  { id: "roadmap", label: "Roadmap" },
  { id: "risks", label: "Risks" },
  { id: "value", label: "Business Value" },
  { id: "next-steps", label: "Next Steps" },
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

  const { architecture_recommendation, model_recommendation, workbench_recommendation, enrichment } = report;
  const hasEnrichment = Boolean(enrichment);

  return (
    <main className="report-shell">
      <button type="button" className="rpt-back-link" onClick={() => navigate("/")}>
        ← Back
      </button>

      <ReportHeader report={report} onPrint={() => window.print()} onReset={reset} />

      {report.decision_kernel && <SufficiencyBanner sufficiency={report.decision_kernel.sufficiency} />}

      <nav className="rpt-nav" aria-label="Report sections">
        {NAV_SECTIONS.map((s) => (
          <a key={s.id} href={`#${s.id}`}>
            {s.label}
          </a>
        ))}
      </nav>

      {/* ================================================================ */}
      {/* Executive summary                                                 */}
      {/* ================================================================ */}
      <div className="rpt-section" id="overview">
        <div className="rpt-section-head">
          <Target width={18} height={18} className="icon" />
          <h2>Executive summary</h2>
        </div>
        <p className="rpt-section-subtitle">The problem, the opportunity, and what's recommended, at a glance.</p>
        <ExecutiveCardsGrid cards={report.executive_cards} />
      </div>

      {/* ================================================================ */}
      {/* Architecture — hero section                                      */}
      {/* ================================================================ */}
      <div className="rpt-section" id="architecture">
        <div className="rpt-section-head">
          <Network width={18} height={18} className="icon" />
          <h2>Recommended architecture</h2>
        </div>
        <p className="rpt-section-subtitle">
          If you were building this tomorrow, here's what the architecture would look like — assembled from the
          specific components recommended below. Click any component for details, or switch views for security,
          AI-catalog, or data-flow emphasis.
        </p>
        <SolutionBlueprint report={report} />

        <div className="rpt-card recommended" style={{ marginTop: "1.25rem" }}>
          <div className="heading" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
            <h3 style={{ margin: 0 }}>{architecture_recommendation.pattern.name}</h3>
            <span className="rpt-badge good">
              <CheckCircle2 width={14} height={14} strokeWidth={2} />
              Selected
            </span>
          </div>
          <p style={{ color: "var(--rpt-ink-soft)", fontSize: "0.9rem", lineHeight: 1.55 }}>
            {architecture_recommendation.pattern.description}
          </p>
          <p style={{ fontSize: "0.88rem", color: "var(--rpt-ink)", background: "var(--rpt-accent-soft)", borderLeft: "3px solid var(--rpt-accent)", padding: "0.65rem 0.9rem", borderRadius: "0 8px 8px 0" }}>
            {architecture_recommendation.rationale}
          </p>
          <DecisionTraceCard trace={architecture_recommendation.decision_trace} />
        </div>
      </div>

      {/* ================================================================ */}
      {/* Decision Kernel — pattern admissibility, sourcing, elimination,   */}
      {/* alternatives, precedents. A projection of the kernel's own        */}
      {/* staged output, not a separate narrative.                         */}
      {/* ================================================================ */}
      {report.decision_kernel && (
        <div className="rpt-section" id="decision-kernel">
          <div className="rpt-section-head">
            <Workflow width={18} height={18} className="icon" />
            <h2>How this was decided</h2>
          </div>
          <p className="rpt-section-subtitle">
            Every pattern the library was checked against, including the ones ruled out and why — plus how each
            required capability was sourced, what was eliminated, and what the real alternatives are.
          </p>
          <DecisionKernelPanel kernel={report.decision_kernel} />
        </div>
      )}

      {/* ================================================================ */}
      {/* Solution components                                              */}
      {/* ================================================================ */}
      <div className="rpt-section" id="components">
        <div className="rpt-section-head">
          <Puzzle width={18} height={18} className="icon" />
          <h2>Solution components</h2>
        </div>
        <p className="rpt-section-subtitle">Reusable AI Catalog components this solution is built from.</p>
        <SolutionComponentCard items={report.enterprise_reuse} />
      </div>

      {/* ================================================================ */}
      {/* Recommended AI models                                            */}
      {/* ================================================================ */}
      <div className="rpt-section" id="models">
        <div className="rpt-section-head">
          <Cpu width={18} height={18} className="icon" />
          <h2>Recommended AI models</h2>
        </div>
        <p className="rpt-section-subtitle">
          {model_recommendation.primary.name} is recommended; alternatives are shown for comparison.
        </p>
        <ModelComparisonTable modelRecommendation={model_recommendation} />
      </div>

      {/* ================================================================ */}
      {/* Workbench configuration                                          */}
      {/* ================================================================ */}
      <div className="rpt-section" id="workbench">
        <div className="rpt-section-head">
          <Settings2 width={18} height={18} className="icon" />
          <h2>Workbench configuration</h2>
        </div>
        <p className="rpt-section-subtitle">How this solution would be provisioned and governed.</p>
        <WorkbenchGroup
          workbench={workbench_recommendation}
          primaryModel={model_recommendation.primary}
          governance={enrichment?.governance_recommendations}
        />
      </div>

      {/* ================================================================ */}
      {/* Evidence & confidence                                            */}
      {/* ================================================================ */}
      <div className="rpt-section" id="evidence">
        <div className="rpt-section-head">
          <Eye width={18} height={18} className="icon" />
          <h2>Evidence &amp; confidence</h2>
        </div>
        <p className="rpt-section-subtitle">How much to trust this recommendation, and what it's grounded in.</p>
        <EvidenceConfidenceGrid report={report} />
        <div style={{ marginTop: "0.9rem" }}>
          <RecommendationQualityPanel report={report} />
        </div>
      </div>

      {/* ================================================================ */}
      {/* Alternative solutions                                            */}
      {/* ================================================================ */}
      <div className="rpt-section" id="alternatives">
        <div className="rpt-section-head">
          <Scale width={18} height={18} className="icon" />
          <h2>Alternative solutions</h2>
        </div>
        <p className="rpt-section-subtitle">Other AI models considered, with their trade-offs against the recommendation.</p>
        <AlternativeSolutionCard modelRecommendation={model_recommendation} />
      </div>

      {/* ================================================================ */}
      {/* Enterprise fit & precedent                                        */}
      {/* ================================================================ */}
      {hasEnrichment &&
        (enrichment!.similar_solutions.length > 0 ||
          enrichment!.reusable_assets.length > 0 ||
          enrichment!.best_practices.length > 0) && (
          <div className="rpt-section" id="precedent">
            <div className="rpt-section-head">
              <Library width={18} height={18} className="icon" />
              <h2>Enterprise fit &amp; precedent</h2>
            </div>
            <p className="rpt-section-subtitle">
              Comparable implementations, reusable AI Catalog assets, and industry guidance behind this recommendation.
            </p>

            {enrichment!.similar_solutions.length > 0 && (
              <div className="rpt-component-grid" style={{ marginBottom: "0.9rem" }}>
                {enrichment!.similar_solutions.map((sol) => (
                  <div className="rpt-card" key={sol.id}>
                    <p style={{ fontWeight: 700, fontSize: "0.92rem", margin: "0 0 0.3rem" }}>{sol.title}</p>
                    <span className="rpt-badge neutral" style={{ marginBottom: "0.5rem" }}>
                      {sol.industry}
                    </span>
                    <p style={{ fontSize: "0.85rem", color: "var(--rpt-ink-soft)", margin: "0.4rem 0" }}>
                      {sol.business_outcome}
                    </p>
                    {sol.lessons_learned[0] && (
                      <p style={{ fontSize: "0.82rem", color: "var(--rpt-ink-muted)", fontStyle: "italic", margin: 0 }}>
                        Lesson learned: {sol.lessons_learned[0]}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {enrichment!.reusable_assets.length > 0 && (
              <div className="rpt-card" style={{ marginBottom: "0.9rem" }}>
                <p style={{ fontWeight: 700, fontSize: "0.88rem", margin: "0 0 0.5rem" }}>Reusable AI Catalog assets</p>
                <ul className="rpt-bullet-list">
                  {enrichment!.reusable_assets.map((a) => (
                    <li key={a.id}>
                      <strong>{a.name}</strong> ({a.asset_type.replace(/_/g, " ")}) — {a.rationale}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {(enrichment!.security_summary.considerations.length > 0 ||
              enrichment!.security_summary.relevant_controls.length > 0) && (
              <div className="rpt-card" style={{ marginBottom: "0.9rem" }}>
                <p style={{ fontWeight: 700, fontSize: "0.88rem", margin: "0 0 0.5rem" }}>Security considerations</p>
                <div className="rpt-chip-row" style={{ marginBottom: "0.6rem" }}>
                  <span className="rpt-badge neutral">{enrichment!.security_summary.security_profile_name} profile</span>
                  {enrichment!.security_summary.compliance_flags.map((f) => (
                    <span className="rpt-badge accent" key={f}>
                      {f}
                    </span>
                  ))}
                </div>
                {enrichment!.security_summary.considerations.length > 0 && (
                  <ul className="rpt-bullet-list">
                    {enrichment!.security_summary.considerations.map((c) => (
                      <li key={c}>{c}</li>
                    ))}
                  </ul>
                )}
                {enrichment!.security_summary.relevant_controls.length > 0 && (
                  <ul className="rpt-bullet-list" style={{ marginTop: "0.5rem" }}>
                    {enrichment!.security_summary.relevant_controls.map((c) => (
                      <li key={c.id}>
                        <strong>{c.title}</strong> — {c.summary}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {enrichment!.best_practices.length > 0 && (
              <div className="rpt-card">
                <p style={{ fontWeight: 700, fontSize: "0.88rem", margin: "0 0 0.5rem" }}>Industry best practices consulted</p>
                <ul className="rpt-bullet-list">
                  {enrichment!.best_practices.map((bp) => (
                    <li key={bp.id}>
                      <strong>{bp.title}</strong> — {bp.summary}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

      {/* ================================================================ */}
      {/* Roadmap                                                          */}
      {/* ================================================================ */}
      {hasEnrichment && enrichment!.implementation_roadmap.phases.length > 0 && (
        <div className="rpt-section" id="roadmap">
          <div className="rpt-section-head">
            <CalendarClock width={18} height={18} className="icon" />
            <h2>Implementation roadmap</h2>
          </div>
          <p className="rpt-section-subtitle">
            Total estimated timeline: {enrichment!.implementation_roadmap.total_timeline}
          </p>
          <RoadmapTimeline phases={enrichment!.implementation_roadmap.phases} />
        </div>
      )}

      {/* ================================================================ */}
      {/* Risks                                                            */}
      {/* ================================================================ */}
      <div className="rpt-section" id="risks">
        <div className="rpt-section-head">
          <ShieldAlert width={18} height={18} className="icon" />
          <h2>Risks</h2>
        </div>
        <p className="rpt-section-subtitle">Key risks to this recommendation and how each is mitigated.</p>
        <RiskTable risks={report.risks} />
      </div>

      {/* ================================================================ */}
      {/* Business value                                                   */}
      {/* ================================================================ */}
      <div className="rpt-section" id="value">
        <div className="rpt-section-head">
          <TrendingUp width={18} height={18} className="icon" />
          <h2>Business value</h2>
        </div>
        <p className="rpt-section-subtitle">Directional estimates grounded in this recommendation's architecture and cost profile.</p>
        <BusinessValueKpis value={report.business_value} />
      </div>

      {/* ================================================================ */}
      {/* Assumptions & next steps                                         */}
      {/* ================================================================ */}
      <div className="rpt-section" id="next-steps">
        <div className="rpt-section-head">
          <ListChecks width={18} height={18} className="icon" />
          <h2>Assumptions &amp; next steps</h2>
        </div>
        <div className="rpt-component-grid">
          <div className="rpt-card">
            <h3 style={{ fontSize: "0.9rem", marginTop: 0, marginBottom: "0.6rem" }}>Assumptions</h3>
            <ul className="rpt-bullet-list">
              {report.assumptions.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </div>
          <div className="rpt-card">
            <h3 style={{ fontSize: "0.9rem", marginTop: 0, marginBottom: "0.6rem" }}>Next steps</h3>
            <ol className="rpt-checklist">
              {report.next_best_actions.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </main>
  );
}
