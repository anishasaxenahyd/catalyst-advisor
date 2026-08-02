import { useNavigate, useParams } from "react-router-dom";
import { useRecommendation } from "../lib/RecommendationContext";
import { getScenario } from "../lib/scenarios";
import SectionCard from "../components/scenarios/SectionCard";
import StakeholderList from "../components/scenarios/StakeholderList";
import KpiComparisonGrid from "../components/scenarios/KpiComparisonGrid";
import DatasetPreviewTable from "../components/scenarios/DatasetPreviewTable";
import ScoredApproachTable from "../components/scenarios/ScoredApproachTable";
import {
  IconAlertTriangle,
  IconArrowRight,
  IconBarChart,
  IconChevron,
  IconDatabase,
  IconLayers,
  IconLightbulb,
  IconRoute,
  IconServer,
  IconSparkles,
  IconTarget,
  IconUser,
} from "../components/icons";

export default function ScenarioBrief() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { submit } = useRecommendation();
  const scenario = id ? getScenario(id) : undefined;

  if (!scenario) {
    return (
      <main className="page">
        <div className="empty-state">
          <p>Scenario not found.</p>
          <button className="primary" onClick={() => navigate("/")}>
            Go to landing
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="page" style={{ maxWidth: 980 }}>
      <button className="back-link" onClick={() => navigate("/")}>
        <IconChevron width={14} height={14} style={{ transform: "rotate(180deg)" }} />
        Back
      </button>

      <div className="scenario-header">
        <p className="eyebrow">
          <IconSparkles width={14} height={14} />
          Demonstration Scenario
        </p>
        <h1>{scenario.title}</h1>
        <p className="tagline">{scenario.tagline}</p>
      </div>

      <SectionCard icon={IconLightbulb} title="Business background &amp; current process">
        <p className="subtitle" style={{ marginBottom: "1rem" }}>{scenario.businessBackground}</p>
        <div className="section-card">
          <h3>Current process</h3>
          <ol className="plain-list">
            {scenario.currentProcess.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
      </SectionCard>

      <SectionCard icon={IconAlertTriangle} title="Pain points &amp; business objectives">
        <div className="two-col-grid">
          <div className="section-card">
            <h3>Pain points</h3>
            <ul className="plain-list">
              {scenario.painPoints.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          </div>
          <div className="section-card">
            <h3>
              <IconTarget width={14} height={14} style={{ marginRight: "0.4em", verticalAlign: "-2px" }} />
              Business objectives
            </h3>
            <ul className="plain-list">
              {scenario.businessObjectives.map((o) => (
                <li key={o}>{o}</li>
              ))}
            </ul>
          </div>
        </div>
      </SectionCard>

      <SectionCard icon={IconUser} title="Stakeholders">
        <StakeholderList stakeholders={scenario.stakeholders} />
      </SectionCard>

      <SectionCard icon={IconServer} title="Existing technology landscape">
        <div className="tech-chip-row">
          {scenario.technologyLandscape.map((t) => (
            <span className="tag-chip" key={t}>
              {t}
            </span>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        icon={IconDatabase}
        title="Sample synthetic datasets"
        subtitle="Illustrative, fully synthetic sample records — not real member, provider, or claims data."
      >
        {scenario.datasets.map((d) => (
          <div key={d.name} style={{ marginBottom: "1rem" }}>
            <DatasetPreviewTable dataset={d} />
          </div>
        ))}
      </SectionCard>

      <SectionCard icon={IconBarChart} title="Current-state KPI dashboard">
        <KpiComparisonGrid kpis={scenario.kpiBaseline} />
      </SectionCard>

      <SectionCard icon={IconLayers} title="Business capability assessment">
        <div className="capability-list">
          {scenario.capabilityAssessment.map((c) => (
            <div className="capability-row" key={c.capability}>
              <span className="name">{c.capability}</span>
              <span className={`maturity-badge ${c.maturity}`}>{c.maturity}</span>
              <span className="notes">{c.notes}</span>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        icon={IconRoute}
        title="AI opportunity analysis"
        subtitle="Three candidate AI approaches, scored against business fit, implementation complexity, security, compliance, scalability, cost, and time-to-value."
      >
        <ScoredApproachTable
          approaches={scenario.approaches}
          recommendedApproach={scenario.recommendedApproach}
          recommendationRationale={scenario.recommendationRationale}
          investmentEstimate={scenario.investmentEstimate}
        />
      </SectionCard>

      <div className="advisor-cta">
        <h2>Run the AI Solution Advisor</h2>
        <p>
          See the full technical recommendation: architecture pattern, AI model, enterprise architecture diagram,
          data-flow and security views, Workbench configuration, implementation roadmap, risks, and business value —
          generated live by the deterministic recommendation engine for this exact scenario.
        </p>
        <button className="primary" onClick={() => submit(scenario.request)}>
          Run the AI Solution Advisor
          <IconArrowRight width={16} height={16} />
        </button>
      </div>
    </main>
  );
}
