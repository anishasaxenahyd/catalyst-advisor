# Product Design Spec — Catalyst AI Solution Advisor

Status: reflects the implementation as it exists today (backend + frontend, all tests green, deployed to Render + Vercel). This is a living document — the codebase is the source of truth; this spec should be updated whenever a design decision described here changes.

## 1. What this product is

Catalyst AI Solution Advisor is a proof-of-concept enterprise consulting accelerator: a user describes an AI idea (or uploads an existing architecture, or opens a pre-built demo scenario), and the app returns a full executive-grade report — recommended architecture pattern, AI model, enterprise Workbench configuration, an interactive architecture diagram, implementation roadmap, risks, business value/ROI, and governance guidance — with the reasoning behind every choice made explicit.

The app is explicitly labeled a "demo, fictional platform" (topbar tagline) — every recommendation, catalog entry, and data point is synthetic. It is not connected to any real enterprise system.

**The governing architectural invariant, unchanged since Phase 0 and enforced across every feature added since:**

> A deterministic engine owns every recommendation and every number. An LLM is used in exactly the places where narration or extraction is the job — it never decides a recommendation, never picks a winner, and never invents a number that isn't traceable to a scoring/config table.

Every feature described below was designed to preserve this invariant, including the two significant additions built after the original Phase 0-3 POC: the prompt optimizer and the demo-scenario system.

## 2. Tech stack

| Layer | Stack |
|---|---|
| Backend | Python 3.13, FastAPI ≥0.115, Pydantic ≥2.9, httpx (hand-rolled REST client, no vendor SDK), pytest |
| Frontend | React 18, TypeScript 5.7, Vite 6, react-router-dom 6, `lucide-react` (report page only) |
| LLM provider | Groq (`llama-3.3-70b-versatile`) via raw REST — `MockLLMProvider` is the deterministic offline/fallback provider, and the app degrades to it automatically if Groq is unavailable or `GROQ_API_KEY` is unset |
| Deployment | Render (backend, `render.yaml`, free web service) + Vercel (frontend, `frontend/vercel.json`), both auto-deploy on push to `main` |
| Persistence | None. Every request is stateless — scored fresh and returned. All "content" (catalogs, registries, scenarios) is static JSON/TypeScript, not a database |

## 3. Backend architecture

### 3.1 Request lifecycle
`POST /api/recommendations` (`backend/app/api/routes.py`) → `build_report()` (`backend/app/engine/recommend.py`), the single orchestrator:

1. **Understand (LLM)** — `LLMProvider.extract_signal_vector()` turns free text + optional hints into a `RawExtractedSignal`, which `app/validation/signal_normalizer.py` turns into a strict `SignalVector` — every field gets a resolved value, a provenance tag (`user`/`llm`/`default`), and any correction is recorded as a `ValidationWarning`. User-supplied hints always win over LLM inference.
2. **Score (deterministic, `app/engine/scoring.py`)** — `rank_candidates()` scores every architecture pattern, AI model, and enterprise asset against the `SignalVector` on six weighted dimensions (`technical_fit`, `enterprise_reuse`, `security_compliance`, `cost_efficiency`, `implementation_complexity`, `scalability`; weights in `backend/data/config/scoring_weights.json`). Compliance is a hard cliff, not graduated: an item missing a required compliance flag for the signaled `data_sensitivity` (e.g. `HIPAA-eligible` for `phi`) scores 20/100 on that dimension regardless of everything else.
3. **Select Workbench (deterministic, `app/engine/workbench_selector.py`)** — rule-based (not weighted-scored) selection of security profile, workspace tier, compute profile, and deployment targets, driven by `data_sensitivity`/`expected_scale`/the chosen model's cost tier.
4. **Compute readiness & business value (deterministic, `app/engine/readiness.py` + `business_value.py`)** — `ImplementationReadiness` is a weighted composite of confidence, feasibility, and inverted complexity, banded through a shared 4-tier scale (95-100 Very High / 90-94 High / 80-89 Good / &lt;80 Needs More Information — `app/engine/confidence_bands.py`, mirrored exactly in the frontend's `lib/confidenceLabel.ts`). `BusinessValueSummary` (cost savings, productivity, accuracy confidence, timeline, ROI) is grounded entirely in existing config tables (`decision_rules.json`) or already-computed scores — never a free-invented number, and always labeled "(estimated)" in the UI.
5. **Narrate (LLM)** — `LLMProvider.generate_executive_report()` takes the fully-decided `EngineOutput` (plus the deterministic `BusinessUnderstanding` restatement) and returns an `ExecutiveNarrative`: `report_title`, `one_line_summary`, four `executive_cards` (problem/opportunity/recommended pattern/expected outcome), structured `risks` (risk/impact/likelihood/mitigation — `status` is stamped deterministically as `"Open"` afterward, never LLM-authored), `assumptions`, `next_best_actions`. The LLM is instructed explicitly not to contradict any decided fact.
6. **Enrich (deterministic, `app/enrichment/service.py`)** — additive context assembled from three independent, static datasets (§3.2): reusable AI Catalog assets and Solution Registry precedents (matched by tag overlap / architecture-pattern + industry), a deterministic `BusinessUnderstanding`/`SecuritySummary`/`GovernanceRecommendation[]`/`ImplementationRoadmap`/`EvidenceConfidenceSummary`.
7. Assemble and return the final `Report` (`backend/app/models/schemas.py`, ~19 top-level fields — see §3.3).

### 3.2 The three static knowledge datasets — distinct, not interchangeable
This is the most commonly-confused part of the backend and worth stating precisely:

| Dataset | Location | Loader | Used for |
|---|---|---|---|
| **Scoring catalog** | `backend/data/catalog/*.json` (architecture_templates, models, agents, apis, mcp_servers, skills) | `app/providers/knowledge/json_providers.py` | The only dataset that actually feeds `rank_candidates()` / scoring. Small and deliberately domain-agnostic — a fixed 22-tag vocabulary (`agentic`, `batch`, `classification`, `copilot`, `document-heavy`, `realtime`, `retrieval`, `structured`, etc.), no industry-specific tags. |
| **AI Catalog** | `backend/data/ai_catalog/*.json` (agents, ai_models, apis, connectors, mcp_servers, prompt_templates, skills) | `app/ai_catalog/factory.py` | Never scored. Matched by tag overlap for the report's "Reusable AI Catalog assets" content only. |
| **Solution Registry** | `backend/data/solution_registry/solutions.json` (29 entries) | `app/solution_registry/factory.py` | Never scored. Matched by a hard `architecture_pattern_id` filter, then ranked `(industry_match, tag_overlap)`, for the report's "Similar enterprise solutions" precedent (capped at 3 per report). |
| **Enterprise Knowledge Platform** | `backend/data/enterprise_knowledge/*.json` (architecture_patterns, ai_models, security_controls, governance_rules, cloud_services, reference_architectures) | `app/enterprise_knowledge/` (its own ingestion/retrieval subsystem, real-vendor-sourced content — Microsoft/AWS/Google Cloud/Anthropic/OpenAI/vendor-neutral) | Never scored. Tag-bridged (`app/enrichment/security.py`/`governance.py` translate signal/pattern context into this dataset's own, disjoint tag vocabulary) into the report's Security View content and Governance recommendations. |

Adding industry-specific realism (e.g. the healthcare-payer demo scenario, §6) means adding entries to the AI Catalog / Solution Registry / EKP — **never** to the scoring catalog, whose vocabulary is intentionally generic across all industries.

### 3.3 `Report` — the contract, unchanged in shape since the redesign
`mode`, `signal_vector`, `report_title`, `one_line_summary`, `executive_cards`, `feasibility`, `implementation_readiness`, `architecture_recommendation`, `enterprise_reuse`, `model_recommendation`, `workbench_recommendation`, `effort_estimate`, `timeline_estimate`, `risks` (`Risk[]`), `assumptions`, `confidence_scores`, `next_best_actions`, `business_value`, `enrichment` (optional — `RecommendationEnrichment`, only absent if the knowledge provider is unavailable).

### 3.4 LLM provider abstraction
`app/providers/llm/base.py`'s `LLMProvider` ABC exposes exactly three operations — `extract_signal_vector`, `generate_executive_report`, `optimize_prompt` (§4). `engine/**` never imports a concrete provider, only the ABC and `factory.get_llm_provider()`. Two implementations: `GroqProvider` (real, REST, retry-with-backoff on transient failures) and `MockLLMProvider` (deterministic keyword-heuristic stand-in, exercises the identical validation/normalization path as the real provider). `FallbackLLMProvider` wraps both — any Groq failure degrades to the mock per-request, logged, never surfaced as an error to the user. `LLM_PROVIDER=mock` forces the mock outright (used for all local/CI testing in this repo, no API key required).

### 3.5 Other backend subsystems worth knowing
- **Design-review intake** (`app/intake/diagram_text_parser.py`): a second submission mode (`mode: "design_review"`) that accepts pasted/uploaded Draw.io XML or Mermaid text, converts it to a text description, and prefixes it onto the free-text description before it enters the same `build_report()` pipeline. No separate scoring path.
- **Enterprise Knowledge Platform pipeline** (`app/enterprise_knowledge/pipeline/`): currently a `NotImplementedRecommendationPipeline` placeholder — a real LLM-assisted RAG flow over this dataset is a stated future direction, not built. Its retrieval layer (`retrieval/in_memory.py`, tag-overlap keyword search) is already wired into the main report enrichment though (§3.2).
- **Knowledge routes** (`app/api/knowledge_routes.py`, mounted at `/api/knowledge`): a separate, smaller API surface (`/categories`, `/search`, `/recommend`) exposing the Enterprise Knowledge Platform directly — independent of the main recommendation flow, not used by any current frontend page.

## 4. Feature: Prompt Optimizer

An optional, pre-submission step on the idea-input screen (`POST /api/prompt-optimizer`, stateless, LLM-backed). Given the user's raw description, hints, and any prior answered clarifying questions, it returns:
- A denser rewrite of the prompt (`optimized_text`), with a before/after token-count estimate (`app/providers/llm/token_utils.py` — a documented `chars/4` heuristic, not a real tokenizer, since no local tokenizer exists for Llama models).
- Up to 3 clarifying questions (`clarifying_questions`), targeted specifically at whichever of the six `SignalVector` fields `signal_normalizer.TRACKED_FIELDS` tracks for confidence (`data_sensitivity`, `data_modality`, `latency_requirement`, `expected_scale`, `automation_level`, `industry`) are still ambiguous — so answering them measurably raises the eventual report's confidence score, closing the loop between "what's missing" and "what the user gets asked."

The frontend (`IdeaInput.tsx`) lets the user optimize, answer/skip questions, re-optimize, and either submit the optimized text or skip the whole step — the skip path is byte-identical to pre-optimizer behavior. `optimize_prompt` never touches `scoring.py` or influences the recommendation; it is advisory only, same invariant as everywhere else.

## 5. Feature: Executive Report page (redesigned)

The `/report` page (`frontend/src/pages/Report.tsx`) is a from-scratch redesign into a Microsoft/Gartner-style consulting deliverable: full-width, left-aligned, its own isolated design system (`frontend/src/report.css` — a deep-blue/slate enterprise palette, deliberately distinct from the rest of the app's warm terracotta brand; only this page imports it) and its own icon set (`lucide-react`, scoped to this page and its sub-components only — every other page keeps the app-wide hand-rolled `components/icons.tsx`).

Section order: Header (LLM-generated title/one-line-summary + Date/Complexity/Implementation Readiness) → Executive Summary (4 cards) → Architecture (hero, interactive diagram) → Solution Components → Recommended AI Models (comparison table) → Workbench Configuration (5 grouped cards: AI Models/Knowledge Sources/Security/Deployment/Monitoring) → Evidence & Confidence (business-language, 4-tier banded) → Alternative Solutions (AI models only — the only alternative type with cost/strengths/weaknesses data) → Enterprise Fit & Precedent (Similar Solutions, Reusable AI Catalog assets, Security considerations, Best practices) → Implementation Roadmap (5 canonical stages: Discovery/Prototype/Build/Pilot/Rollout, each with risks) → Risks (table) → Business Value (5 KPI cards) → Assumptions & Next Steps.

**Architecture diagram** (`components/SolutionBlueprint.tsx` + `lib/blueprint.ts`): not Mermaid (there is no Mermaid dependency in this app, despite older docs/comments once implying otherwise) — a hand-built, interactive SVG/DOM diagram assembled per-report from the actual recommended components (not a generic template): swimlane zones, click-to-inspect node detail drawer, 4 tabbed views (Solution/Security/AI/Data-flow), a 5-category legend (App/AI/Data/Security/External Systems), and a `ResizeObserver` + CSS `transform: scale` mechanism so it always fits its container width with zero horizontal scroll, at any viewport.

Every data table on this page (model comparison, risks) collapses to stacked label/value rows below 720px instead of scrolling horizontally — a deliberate, repeated pattern, not a one-off.

## 6. Feature: Demo Scenarios

A pre-built, narrated business case that a user can open from the landing page and either read as a standalone consulting brief or feed straight into the real recommendation engine. Currently one scenario is built: **Claims Payment Integrity Advisor**, modeled generically on a large national health payer (fully synthetic — no real payer data, PHI, or proprietary workflows). Full content spec: `docs/demo-scenario-claims-payment-integrity.md`.

Design decisions (both confirmed deliberately, to keep this feature's footprint minimal):
- **The scenario brief itself is 100% frontend-only static data** (`frontend/src/lib/scenarios.ts`, typed via `frontend/src/types/scenario.ts`) — business background, stakeholders, synthetic sample datasets, current-state KPI baseline, capability assessment, and a 3-approach × 7-dimension AI Opportunity Analysis. No new backend route or schema exists for this content.
- **The "Run the AI Solution Advisor" button calls the real, unmodified `submit()`** (`lib/RecommendationContext.tsx`) with a pre-built `RecommendationRequest` — landing on the exact same live `/report` pipeline described in §3, not a mocked or pre-baked result.
- **Backend changes for this scenario are additive JSON only**: one Solution Registry entry (`solution-healthcare-payment-integrity-batch`, on `pattern-batch-classification` specifically so it doesn't compete with unrelated entries for registry display slots), one AI Catalog asset (`asset-mcp-claims-lookup`), one Enterprise Knowledge Platform security control (`control-phi-minimum-necessary-access`, HIPAA minimum-necessary framing). No scoring-engine or schema change.
- **The 7-dimension scored comparison (business fit/complexity/security/compliance/scalability/cost/time-to-value) is authored expert-analysis content**, not computed by the production 6-dimension scoring engine — that engine combines security+compliance into one dimension and has no time-to-value concept, and forking it to add these would be a shared, all-reports-affecting change out of proportion to one demo. This mirrors how a real consulting team's pre-engagement options analysis actually gets produced — before the deep technical scoring engine even runs.

New page: `/scenarios/:id` (`pages/ScenarioBrief.tsx`), reached from a third card on the Landing page. Uses the main app's brand (`index.css`), not the report's isolated palette — a scenario brief reads as app content, not an exported deliverable.

## 7. Frontend structure

```
pages/         Landing, IdeaInput, DesignUpload, Analyzing, ScenarioBrief, Report (lazy-loaded)
components/     ConfidenceBadge, DecisionTraceCard, RecommendationQualityPanel, ScoreBar,
                SolutionBlueprint, icons.tsx (app-wide hand-rolled icon set)
components/report/     Report-page-only, lucide-icon, report.css-styled: ReportHeader,
                        ExecutiveCardsGrid, SolutionComponentCard, ModelComparisonTable,
                        WorkbenchGroup, EvidenceConfidenceGrid, AlternativeSolutionCard,
                        RoadmapTimeline, RiskTable, BusinessValueKpis
components/scenarios/  Scenario-brief-only, index.css-styled: SectionCard, KpiComparisonGrid,
                        DatasetPreviewTable, StakeholderList, ScoredApproachTable
lib/            RecommendationContext (submit/status/report state machine), apiClient,
                blueprint.ts (diagram model+layout), catalogLabels, complexityLabel,
                confidenceLabel (mirrors backend confidence_bands.py exactly), decisionTrace,
                relativeBand, scenarios.ts, severity
types/          report.ts (mirrors backend/app/models/schemas.py by hand), scenario.ts
```

Routing (`App.tsx`): `/` (Landing) → `/idea` or `/design` (intake) → `/analyzing` (loading state, reads context) → `/report` (lazy-loaded, only page that imports `report.css`); `/scenarios/:id` reachable directly from Landing, bypasses intake and jumps straight to `/analyzing`→`/report` via `submit()`.

Two co-existing, deliberately separate design systems: the app-wide warm/terracotta brand (`index.css`, every page except `/report`) and the report's isolated enterprise-blue system (`report.css`, `/report` only). This split was a considered decision (report redesign), not an accident — the report is meant to read as a distinct, brand-neutral deliverable someone might export/print, not as app chrome.

## 8. Testing

Backend: 89 pytest tests (`backend/tests/`), run via `cd backend && .venv/Scripts/python.exe -m pytest -q`. Covers scoring/confidence math, signal normalization, prompt-optimizer normalization, readiness/business-value formulas, enrichment assembly, the fallback provider, Groq provider parsing (mocked HTTP), and route-level tests against `LLM_PROVIDER=mock`.

Frontend: no unit test suite yet (typecheck + build via `npm run build` is the current bar: `tsc --noEmit && vite build`). Feature verification in this project has consistently used a Playwright-driven browser walkthrough (installed as a temporary devDependency, always reverted after use — not a permanent project dependency) to confirm zero console errors and zero horizontal overflow at desktop/tablet/mobile widths before calling any UI feature done.

## 9. What's deliberately not built

- Only one demo scenario exists (Claims Payment Integrity Advisor). The data model (`types/scenario.ts`) supports more; two others (Prior Authorization Review Assistant, Member Service Copilot) were scoped and then explicitly descoped back to one.
- No persistence layer anywhere — by design, not by omission. Every "content" concept in this app (catalogs, registries, scenarios) is static JSON/TypeScript with an in-process `lru_cache`, not a database.
- The Enterprise Knowledge Platform's LLM-assisted RAG pipeline (`app/enterprise_knowledge/pipeline/`) is a placeholder — its retrieval layer is live and wired into report enrichment, but nothing calls it as a standalone recommendation flow yet.
- No real scoring-engine extension to a 7-named-dimension model exists — the demo scenario's comparison table is intentionally authored content, not a shared engine change (§6).
