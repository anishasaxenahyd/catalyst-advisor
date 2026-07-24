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

## Tests

```bash
pytest
```

30 tests: the retry helper, `FallbackLLMProvider`, `GroqProvider`'s error
classification (via monkeypatched `httpx.Client.post` — no network calls in
the suite), the validation/normalization layer, and provenance-weighted
confidence scoring. Live network behavior is verified manually against the
real Groq endpoint; see the phase reports for details.
