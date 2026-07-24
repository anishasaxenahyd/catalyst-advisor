# Catalyst AI Solution Advisor — POC

A lightweight, demo-ready advisor: describe an AI idea or upload an architecture,
get back an executive recommendation against a fictional enterprise AI
platform (Catalyst Catalog + Catalyst Workbench). See `docs/` for the full
design spec.

**Phase 0 status:** foundation complete — provider interfaces, deterministic
scoring engine with Decision Trace, fictional Catalog/Workbench data, and a
basic five-screen frontend shell.

**Phase 1 status:** the `LLMProvider` (`GroqProvider`) is production-hardened
(timeouts, retries, error classification) and wrapped in
`FallbackLLMProvider` so an outage or missing API key degrades to
`MockLLMProvider` per-request rather than breaking the demo. No image
understanding yet (see `backend/README.md`).

**Phase 2 status:** a Validation/Normalization layer sits between the
provider's extraction and the deterministic engine — normalizes casing,
rejects unrecognized values, dedupes, defaults sensibly, and tracks per-field
provenance (user/LLM/default), which now drives confidence scoring.

**Phase 3 status:** the Report page is a full executive dashboard — Decision
Trace as expandable sections, six-dimension scores as bars, a dedicated
recommendation-quality panel (confidence rationale, validation warnings,
corrected/discarded values), and rendered Mermaid diagrams with a text
fallback. Frontend-only; no backend or API contract changes.

**POC Cleanup:** Gemini, Grok/x.ai, Claude, OpenAI, and OpenRouter provider
implementations were removed — evaluated during Phase 1 but never the
active choice. `GroqProvider` is now the only production `LLMProvider`,
`MockLLMProvider` its fallback; the vendor-agnostic interface remains, so
adding a provider back is a new class, not an architecture change.

- `backend/` — FastAPI service, `python -m venv .venv && pip install -r requirements.txt && uvicorn app.main:app --reload`
- `frontend/` — Vite + React + TS, `npm install && npm run dev`

Run both, then open http://localhost:5173.
