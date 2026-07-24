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

- `pages/Report.tsx` — the executive dashboard: exec summary, primary
  recommendation strip, feasibility, recommendation quality, architecture
  (with a rendered Mermaid diagram), enterprise reuse, model + alternatives,
  Workbench, risks, confidence breakdown, next actions.
- `components/DecisionTraceCard.tsx` — Decision Trace as five independently
  expandable sections (why selected / alternatives / assumptions / evidence
  / confidence); evidence renders as score-bar meters when it's dimension
  data, or plain facts otherwise (see `lib/decisionTrace.ts`).
- `components/RecommendationQualityPanel.tsx` — confidence, confidence
  rationale, missing information, validation warnings, and a corrected/
  discarded-values table, all sourced from fields the API already returned
  in Phase 2 but the frontend never displayed.
- `components/{ScoreBar,ConfidenceBadge,StatTile,MermaidDiagram}.tsx` —
  small reusable primitives; `components/icons.tsx` is a hand-rolled SVG
  icon set (no icon library dependency).
- `lib/severity.ts` — shared 0-100 → good/warning/critical banding, used by
  every score/confidence display for a consistent palette.

Mermaid is dynamically imported (`components/MermaidDiagram.tsx`) and the
whole Report route is lazy-loaded (`App.tsx`) so its cost is paid only when
a report is actually viewed — Landing/forms/Analyzing never download it.
