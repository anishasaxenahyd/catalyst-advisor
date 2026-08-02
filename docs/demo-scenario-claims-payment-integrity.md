# Design Spec — Claims Payment Integrity Advisor Demo Scenario

Status: backend content **implemented**; frontend (types, content module, components, pages, routing) **not yet implemented** — this spec fully defines it.

## 1. Objective

One polished, end-to-end demonstration scenario for an executive audience at a large health-payer organization: **Claims Payment Integrity Advisor** — an AI solution that analyzes historical claims, identifies suspicious patterns, explains risk factors, prioritizes investigations, and recommends next actions for a claims payment-integrity team.

This supersedes the earlier three-scenario plan (`.claude/plans/zesty-sauteeing-marble.md`) — scope is now this one scenario only. All content is synthetic/fictional; no real payer data, PHI, or proprietary workflows.

## 2. What already exists and is being reused (current implementation baseline)

The app's existing recommendation pipeline already produces nearly every deliverable this scenario needs, with zero further backend logic changes required:

- **`backend/app/engine/recommend.py::build_report()`** — the one orchestrator. Given `mode`, `raw_text`, and `hints`, it runs signal extraction → six-dimension deterministic scoring (`backend/app/engine/scoring.py`) → workbench selection → enrichment → LLM narration, and returns a complete `Report` (architecture recommendation, model recommendation, workbench config, roadmap, risks, business value, executive cards, evidence/confidence — the full shape rebuilt in the report redesign earlier this project).
- **PHI-aware compliance is already fully wired**, confirmed by direct testing: setting `hints.data_sensitivity = "phi"` (a) penalizes non-HIPAA-eligible models/patterns in scoring (`scoring.py::_security_compliance`), (b) forces the `security-phi-regulated` workbench security profile (`workbench_selector.py`), and (c) emits a HIPAA-compliance governance recommendation (`enrichment/governance.py`) — all automatically, no code path specific to this demo.
- **The report UI** (`frontend/src/pages/Report.tsx` + `frontend/src/report.css`) already renders the architecture diagram (`SolutionBlueprint`), data-flow/security/AI-component views (diagram tabs), workbench configuration, roadmap, risk table, business value KPIs, and executive summary — this is the "final professional report" deliverable, unmodified.
- **`frontend/src/lib/RecommendationContext.tsx`'s `submit(request: RecommendationRequest)`** accepts a fully static, pre-built request from anywhere in the app (confirmed — `IdeaInput.tsx:116-120` is the existing reference call site) and drives `/analyzing` → `/report` unchanged. A new scenario page can call this directly.

## 3. Backend content — implemented

Three additive, schema-unchanged JSON additions so the live report that comes back for this scenario feels genuinely tailored:

- **Solution Registry** (`backend/data/solution_registry/solutions.json`): `solution-healthcare-payment-integrity-batch` — "Claims Payment Integrity Advisor for a National Health Payer," `architecture_pattern_id: "pattern-batch-classification"`, `industry: "Healthcare"`, tags `batch, classification, high-scale, structured`. Surfaces automatically in the live report's Similar Solutions whenever a request lands on the same pattern (industry-match-then-tag-overlap ranking in `enrichment/service.py::_similar_solutions`).
- **AI Catalog** (`backend/data/ai_catalog/mcp_servers.json`): `asset-mcp-claims-lookup` — Claims Lookup MCP Server, tags `integration-heavy, structured, retrieval`. Referenced by the Solution Registry entry above and surfaces in Reusable Assets by tag overlap.
- **Enterprise Knowledge Platform** (`backend/data/enterprise_knowledge/security_controls.json`): `control-phi-minimum-necessary-access` — "Minimum Necessary PHI Access Scoping," tags `phi, healthcare, regulated-industry, access-control, data-protection`. Strengthens Security View specificity beyond the existing generic controls.

Verified: `cd backend && .venv/Scripts/python.exe -m pytest -q` — 89 passed, including the Solution Registry entry-count bound test (29 entries, within the existing 20-30 assertion).

## 4. Frontend data model — to implement (`frontend/src/types/scenario.ts`, new)

```ts
export interface ScenarioStakeholder { role: string; concern: string }
export interface ScenarioDataset { name: string; description: string; columns: string[]; rows: (string | number)[][] }
export interface ScenarioKpi { label: string; current: string; target: string }
export interface ScenarioCapability { capability: string; maturity: "Low" | "Medium" | "High"; notes: string }
export interface ScoredApproach {
  name: string; description: string; pros: string[]; cons: string[];
  scores: { businessFit: number; implementationComplexity: number; security: number;
            compliance: number; scalability: number; cost: number; timeToValue: number };
  // All scores 1-10, higher = more favorable (implementationComplexity: 9 means EASY — a UI caption states this explicitly).
}
export interface Scenario {
  id: string; title: string; tagline: string;
  businessBackground: string; currentProcess: string[]; painPoints: string[];
  businessObjectives: string[]; stakeholders: ScenarioStakeholder[]; technologyLandscape: string[];
  datasets: ScenarioDataset[]; kpiBaseline: ScenarioKpi[]; capabilityAssessment: ScenarioCapability[];
  approaches: ScoredApproach[]; recommendedApproach: string; recommendationRationale: string;
  investmentEstimate: string;
  request: RecommendationRequest; // fed straight into the real submit()
}
```

## 5. Scenario content — fully specified

### Business background
A large national health payer processes millions of medical, behavioral, and ancillary claims monthly. A dedicated Payment Integrity team of claims investigators reviews a subset of paid and pending claims for duplicate billing, upcoding/unbundling, and other overpayment risk — but review coverage is capped by manual investigator capacity, not by claim volume.

### Current process
1. Claims flow from the core claims adjudication platform into a nightly extract for the Payment Integrity team.
2. Investigators manually query multiple systems (claims history, provider network file, prior investigation notes) to check a sampled claim.
3. Investigators cross-reference procedure/diagnosis code combinations against known billing-anomaly patterns from memory and spreadsheets.
4. Suspected claims are escalated to a senior investigator for manual case-file assembly.
5. Confirmed overpayments route to the recovery team; findings are logged in a shared tracker, not systematically fed back into future targeting.
6. Investigation coverage is sampling-based and capped by team size, not comprehensive.

### Pain points
- Only ~4% of paid claims receive any payment-integrity review each month.
- Average investigation takes 6.5 business days from flag to disposition.
- Investigators spend an estimated 40% of their time gathering data across systems rather than analyzing it.
- False-positive rate on manually-flagged claims runs near 35%.
- Dollars recovered per investigator-hour has plateaued for several quarters.
- No systematic way to prioritize the highest-risk claims first — review order is largely FIFO.

### Business objectives
- Increase payment-integrity review coverage from ~4% to 100% of paid claims via automated risk scoring.
- Reduce average investigation turnaround from 6.5 days to under 2 days for prioritized cases.
- Reduce false-positive rate on escalated cases from ~35% to under 15%.
- Increase dollars protected per investigator-hour by at least 30% within two quarters of rollout.
- Maintain a full explainability/audit trail for every flagged claim, to support appeals and regulatory review.

### Stakeholders
| Role | Concern |
|---|---|
| VP, Payment Integrity | Owns the investigator team and recovery targets |
| Director, Special Investigations Unit | Oversees fraud/abuse escalations |
| Chief Compliance Officer | Regulatory and audit accountability |
| CIO / Chief Digital Officer | Technology investment sponsor |
| VP, Claims Operations | Owns the core claims platform and data feeds |
| Actuarial/Finance Lead | Validates dollars-protected methodology and ROI |
| Provider Network Relations Lead | Manages provider-facing impact of flagged claims/appeals |

### Technology landscape
Core claims adjudication platform (Facets-class) &middot; enterprise data warehouse (Snowflake-class) &middot; provider network/credentialing system &middot; investigation tracking (spreadsheet-based today) &middot; enterprise SSO &middot; EDI clearinghouse (Availity-class) &middot; BI/reporting layer (Power BI-class). All plausible product *categories*, not any real company's proprietary systems.

### Sample synthetic datasets (obviously-fake IDs)
1. **Sample Claims** — Claim ID, Member ID, Provider ID, Procedure Code, Diagnosis Code, Billed Amount, Paid Amount, Status, Risk Score (~9 rows).
2. **Sample Providers** — Provider ID, Provider Org Name (synthetic, e.g. "Provider Org 1042"), Specialty, Network Status, 30-Day Claims Volume, Prior Flags (~8 rows).
3. **Sample Investigation Outcomes** — Case ID, Claim ID, Flag Reason, Disposition, Dollars Recovered, Days to Disposition (~8 rows).

### KPI baseline (current → target)
| KPI | Current | Target |
|---|---|---|
| Claims reviewed for payment integrity (monthly) | 4% | 100% |
| Average investigation turnaround | 6.5 days | &lt; 2 days |
| False-positive rate on escalated cases | 35% | &lt; 15% |
| Dollars protected per investigator-hour | $410 | $550+ |
| Investigator time spent on data-gathering | ~40% | &lt; 15% |

### Business capability assessment
| Capability | Maturity | Notes |
|---|---|---|
| Claims Data Integration &amp; Accessibility | Medium | Data exists in the warehouse but requires manual multi-system querying |
| AI/ML Operations Maturity | Low | No production ML models in the payment-integrity function today |
| Investigation Case Management | Low | Spreadsheet-based tracking, no structured case system |
| Data Governance &amp; Explainability | Medium | Strong audit culture, but no explainability tooling for automated flags yet |
| Change Management / Investigator Enablement | Medium | Team is receptive to tooling, limited AI-assisted-workflow experience |

### AI Opportunity Analysis — 3 approaches scored 1-10 (higher = more favorable)

| Approach | Business Fit | Complexity | Security | Compliance | Scale | Cost | Time-to-Value |
|---|---|---|---|---|---|---|---|
| **Batch Risk-Scoring &amp; Prioritization Pipeline** ✅ | 9 | 8 | 8 | 8 | 9 | 8 | 9 |
| Agentic Investigation Copilot (HITL) | 8 | 5 | 8 | 8 | 7 | 6 | 6 |
| Rules Engine + LLM Case Summarization | 6 | 7 | 7 | 7 | 6 | 7 | 7 |

**Recommended: Batch Risk-Scoring &amp; Prioritization Pipeline** — fastest time-to-value, directly closes the 4%-coverage gap at enterprise scale, highest scalability and lowest implementation complexity of the three. Framed explicitly as the foundational phase, with the Agentic Investigation Copilot noted as a natural phase-2 extension once scoring is in production (real consulting framing — a phased roadmap, not a one-shot pitch). This is also the approach the live Advisor request below is written to land on (`pattern-batch-classification`).

### Investment estimate
"$650K-$950K (Year 1: risk-scoring pipeline, data integration, investigator workflow tooling, and change management) — a follow-on agentic-copilot phase is a separate future investment."

### Live Advisor request payload
```ts
{
  mode: "idea",
  description: "A batch AI pipeline that analyzes historical and incoming claims for a national health payer's Payment Integrity team, scoring every paid and pending claim for duplicate-billing, upcoding, and coding-anomaly risk, explaining the contributing risk factors, and producing a prioritized investigation queue so investigators work highest-risk claims first instead of a small random sample.",
  hints: { industry: "Healthcare", data_sensitivity: "phi", expected_scale: "enterprise", automation_level: "assist" }
}
```
(`batch, classification, high-scale, structured` tag alignment per the confirmed scoring-engine vocabulary — lands on `pattern-batch-classification`; `phi` sensitivity activates the PHI compliance/governance/workbench logic described in §2 end-to-end.)

## 6. Frontend components — to implement (`frontend/src/components/scenarios/`, new)

Brand-matched to the main app palette (`index.css`), **not** the report's isolated `report.css` (only `Report.tsx` imports that today):
- `SectionCard.tsx` — titled card wrapper, reused across every brief section.
- `KpiComparisonGrid.tsx` — current-vs-target stat tiles (consult the `dataviz` skill before styling).
- `DatasetPreviewTable.tsx` — generic table renderer, responsive stacked-row collapse on mobile (same technique as the report's `.rpt-table`, ported to main-brand classes) — zero horizontal scroll.
- `StakeholderList.tsx` — role/concern list.
- `ScoredApproachTable.tsx` — the 3×7 comparison, recommended approach visually marked, "higher = more favorable" caption.

## 7. Pages and routing — to implement

- **`pages/ScenarioBrief.tsx`** at route **`/scenarios/claims-payment-integrity`** (single scenario — no gallery page needed at this scope; `App.tsx` gets one new eager route). Section order: header (title/tagline/back-link) → Business Background &amp; Current Process → Pain Points &amp; Objectives → Stakeholders → Technology Landscape → Sample Synthetic Datasets → Current-State KPI Dashboard → Business Capability Assessment → AI Opportunity Analysis → prominent **"Run the AI Solution Advisor"** CTA calling `useRecommendation().submit(scenario.request)`.
- **`Landing.tsx`**: third `.mode-card` in the existing auto-reflowing `.mode-grid`, linking directly to `/scenarios/claims-payment-integrity` (no intermediate gallery for a single scenario).

## 8. Verification plan

- Backend: `cd backend && .venv/Scripts/python.exe -m pytest -q` (already green — no further backend changes expected).
- Frontend: `cd frontend && npm run build`.
- Live walkthrough (Playwright): Landing → new mode-card → brief page (confirm datasets/KPIs/scored comparison render, zero horizontal scroll at desktop/tablet/mobile) → "Run the AI Solution Advisor" → confirm the live `/report` lands on `pattern-batch-classification`, a HIPAA-eligible model, the PHI-flagged security profile, and that `solution-healthcare-payment-integrity-batch` / `asset-mcp-claims-lookup` / `control-phi-minimum-necessary-access` all surface in the report's enrichment sections.
