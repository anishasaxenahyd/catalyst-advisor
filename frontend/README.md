# Catalyst AI Solution Advisor — frontend

Five-screen app (Landing, Idea Input, Design Upload, Analyzing, Report)
wired to the backend's single `/api/recommendations` route. The Report
page is an executive-dashboard-style view — everything the API returns
(recommendations, six-dimension scores, Decision Trace, validation
warnings, confidence rationale) is rendered, not just a subset.

## Run locally

```bash
cd frontend
npm install
cp .env.example .env   # points at the local backend by default
npm run dev
```

Requires the backend running at `VITE_API_BASE_URL` (defaults to
`http://localhost:8000`).

## Structure

- `pages/Report.tsx` — the executive report: header (title, one-line summary,
  complexity/readiness), executive summary cards, architecture (with the
  interactive `SolutionBlueprint` diagram), solution components, AI model
  comparison, Workbench configuration, evidence & confidence, alternative
  solutions, roadmap, risks, business value, and next steps. Uses its own
  design system (`report.css`) and Lucide icons, isolated from the rest of
  the app's warm/terracotta brand and hand-rolled icon set.
- `components/report/*.tsx` — report-only presentational components
  (`ReportHeader`, `ExecutiveCardsGrid`, `SolutionComponentCard`,
  `ModelComparisonTable`, `WorkbenchGroup`, `EvidenceConfidenceGrid`,
  `AlternativeSolutionCard`, `RoadmapTimeline`, `RiskTable`,
  `BusinessValueKpis`), each driven entirely by props off the `Report` type.
- `components/SolutionBlueprint.tsx` + `lib/blueprint.ts` — a hand-built,
  interactive architecture diagram (not Mermaid — there's no Mermaid
  dependency in this app): swimlanes, click-to-inspect nodes, tabbed
  solution/security/AI/data-flow views, and a scale-to-fit canvas (via
  `ResizeObserver` + CSS `transform: scale`) so it never needs horizontal
  scroll.
- `components/DecisionTraceCard.tsx` — Decision Trace as five independently
  expandable sections (why selected / alternatives / assumptions / evidence
  / confidence); evidence renders as score-bar meters when it's dimension
  data, or plain facts otherwise (see `lib/decisionTrace.ts`).
- `components/RecommendationQualityPanel.tsx` — confidence, confidence
  rationale, missing information, validation warnings, and a corrected/
  discarded-values table, all sourced from fields the API already returns.
- `components/{ScoreBar,ConfidenceBadge}.tsx` — small reusable primitives;
  `components/icons.tsx` is the app-wide hand-rolled SVG icon set (used by
  every page except the report, which uses `lucide-react` instead).
- `lib/severity.ts` — shared 0-100 → good/warning/critical banding used
  elsewhere in the app; `lib/confidenceLabel.ts` is the report's own
  Very High/High/Good/Needs More Information banding (mirrors
  `backend/app/engine/confidence_bands.py` exactly).

The whole Report route is lazy-loaded (`App.tsx`) so its design system and
components are only downloaded when a report is actually viewed —
Landing/forms/Analyzing never pay for it.
