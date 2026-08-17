# Running Catalyst AI Solution Advisor locally

This app is hosted locally only — there is no cloud deployment target
(the earlier Render/Vercel setup, `render.yaml` and `frontend/vercel.json`,
has been removed). Run both services on your own machine.

## Prerequisites

- Python 3.13 (or whatever `backend/.venv` was created with) and `pip`.
- Node.js + npm for the frontend.
- Optionally, a Groq API key if you want real LLM output instead of the
  deterministic `MockLLMProvider` (see `backend/.env.example`).

## 1. Backend

```bash
cd backend
python -m venv .venv          # first time only
.venv/Scripts/activate         # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env           # then fill in GROQ_API_KEY, or set LLM_PROVIDER=mock
uvicorn app.main:app --reload --port 8000
```

Confirm it's up: `curl http://localhost:8000/health` should return `{"status":"ok"}`.

Set `LLM_PROVIDER=mock` in `backend/.env` (or as an environment variable) to
run entirely offline with the deterministic mock provider — no API key
needed. This is also what the test suite uses.

## 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

`frontend/.env` already points `VITE_API_BASE_URL` at
`http://localhost:8000`. Open `http://localhost:5173`.

## Tests

```bash
cd backend && pytest
cd frontend && npm run build   # tsc --noEmit + vite build
```

## Notes

- **No database, no persistence** — every request is handled fresh and
  returned. Nothing to migrate or back up.
- **Secrets** live only in `backend/.env` (gitignored) — never commit it.
- If you later want to host this somewhere, the backend is a standard
  FastAPI app (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`) and the
  frontend is a standard Vite build (`npm run build` → serve `dist/`) — any
  platform that runs those works; there's just no configuration for one
  checked in right now.
