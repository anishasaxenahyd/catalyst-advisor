# Catalyst AI Solution Advisor — backend

FastAPI service exposing one route, `POST /api/recommendations`. Everything
downstream of intake is deterministic; the only external dependency is a
swappable `LLMProvider`.

## Run locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Then:

```bash
curl -X POST http://localhost:8000/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{"mode": "idea", "description": "We want a copilot that drafts replies to support tickets in real time.", "hints": {}}'
```

## LLM provider

`GroqProvider` (api.groq.com) is the only production `LLMProvider` in this
POC; `MockLLMProvider` is the fallback when it's unavailable (see
`.env.example`). The `LLMProvider` interface itself remains
vendor-agnostic — adding a second provider later is a new class behind the
same two methods, not an architecture change — but this POC intentionally
keeps only one production implementation to stay simple to run and
demonstrate. (Gemini, Grok/x.ai, Claude, OpenAI, and OpenRouter were
evaluated during earlier phases and removed in the POC Cleanup pass — see
git history for that exploration.)

Two independent safety nets, so the app always returns a valid report:

- **Not configured** (`GROQ_API_KEY` unset) — logged once at request time,
  `MockLLMProvider` is used for the life of the process. No crash on boot.
- **Configured but failing at request time** (timeout, outage, malformed
  output) — `GroqProvider` retries transient failures itself (exponential
  backoff); if it still can't produce a result, `FallbackLLMProvider`
  degrades to `MockLLMProvider` for that one request. Non-retryable
  failures (bad API key, bad request) skip straight to fallback without
  wasting retries.

Set `LLM_PROVIDER=mock` to force the deterministic mock (e.g. CI, or local
dev without a key). Set `LLM_FALLBACK_TO_MOCK=false` to let request-time
failures raise instead of silently degrading.

## Validation layer (Phase 2)

Every provider's extraction is routed through `app/validation/signal_normalizer.py`
before the engine ever sees it — normalizes casing/whitespace, matches
values against the known vocabulary (rejecting anything unrecognized, e.g.
a tag the LLM invented that isn't in the Catalog), removes duplicate tags
and integration points, and applies sensible defaults for anything that
still can't be resolved. Every correction or default is recorded as a
`ValidationWarning` on `SignalVector.validation_warnings`, and each field's
origin — `user` (from a hint), `llm` (from the provider), or `default` — is
recorded in `SignalVector.field_provenance`. Confidence scoring
(`engine/scoring.py`) is weighted by that provenance (user > llm > default),
and every `DecisionTrace` carries `missing_information`,
`validation_warnings`, and a `confidence_rationale` string derived from it.

User-supplied hints always win over whatever the LLM inferred for the same
field — the prompt already asks providers to echo hints verbatim, but nothing
enforced that before this layer existed.

## Enterprise Knowledge Platform (foundation)

`app/enterprise_knowledge/` is a separate, additive module — a vendor-neutral
knowledge base (Architecture Patterns, AI Models, Security Controls,
Governance Rules, Cloud Services, AI Catalog Components, Reference
Architectures) seeded with curated public knowledge from Microsoft, AWS,
Google Cloud, Anthropic, and OpenAI (`data/enterprise_knowledge/*.json`,
47 entries). It does not touch, and is not touched by, the deterministic
engine (`app/engine/`) or the Catalyst-specific catalog
(`app/providers/knowledge/`) — those still serve `/api/recommendations`
exactly as before.

- **Ingestion** (`ingestion/`): `KnowledgeSourceLoader` interface with
  working JSON and YAML implementations. A new source format is one small
  loader class, not a rewrite.
- **Retrieval** (`retrieval/`): `RetrievalService` with a real
  `InMemoryKeywordRetrievalService` (category/vendor/tag filtering + keyword
  scoring). `VectorSearchCapable` and `GraphTraversalCapable` are defined
  extension points — a future implementation can add either without
  changing the interface or any caller.
- **Pipeline** (`pipeline/`): `RecommendationPipeline` interface plus
  `Evidence`/`ConfidenceScore` output types, for a future LLM-assisted,
  retrieval-augmented recommendation flow. `NotImplementedRecommendationPipeline`
  is the only implementation today — it returns a valid, clearly-labeled
  placeholder rather than reasoning over anything.
- **API**: `GET /api/knowledge/categories`, `GET /api/knowledge/search`,
  `POST /api/knowledge/recommend` — new routes under `/api/knowledge`,
  mounted alongside (not replacing) the existing router.

## AI Catalog & Solution Registry

Two more additive, JSON-seeded modules, each with the same
loader-with-`lru_cache` shape as everything else in this codebase:

- **AI Catalog** (`app/ai_catalog/`, `data/ai_catalog/*.json`) — 28 sample
  reusable enterprise assets (agents, MCP servers, APIs, models, prompt
  templates, skills, connectors). Independent of both the Catalyst-specific
  catalog and the Enterprise Knowledge Platform — this is a fictional
  enterprise's own asset inventory.
- **Solution Registry** (`app/solution_registry/`, `data/solution_registry/solutions.json`)
  — 28 fictional-but-realistic past implementations across 16 industries and
  all 5 architecture patterns, each with a business problem, security
  considerations, outcome, and lessons learned.

## Recommendation enrichment

`app/enrichment/` deterministically enriches every `Report` with an
`enrichment` field built from the three sources above plus the engine's own
config-driven rules — no LLM call, no new scoring dimension. It's the one
intentional touch to `app/engine/recommend.py` (one import, one function
call, one field on the final `Report`). Per-concern builders:

- `business.py` — a templated restatement of the `SignalVector`
- `security.py` — workbench + Solution Registry + Enterprise Knowledge
  Platform security controls, matched via a tag-vocabulary bridge (the EKP's
  own tags don't overlap the engine's controlled tag set)
- `governance.py` — compliance-flag rules, automation/scale policy tables in
  `decision_rules.json`, and matched EKP governance rules
- `roadmap.py` — phase templates looked up by the pattern's complexity tier
- `evidence.py` — a consolidated confidence/evidence-strength summary

## Tests

```bash
pytest
```

67 tests: everything above, plus the retry helper, `FallbackLLMProvider`,
`GroqProvider`'s error classification (via monkeypatched `httpx.Client.post`
— no network calls in the suite), the validation/normalization layer, and
provenance-weighted confidence scoring. Live network behavior is verified
manually against the real Groq endpoint; see the phase reports for details.
