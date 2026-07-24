# Deployment runbook — Catalyst AI Solution Advisor

Target: **Vercel** (frontend, static) + **Render** (backend, Python web service).
Both deploy from a shared GitHub repo. Order matters — backend first, so the
frontend has a real API URL to point at.

## 0. Prerequisites

- A GitHub account (repo hosting + what Vercel/Render both deploy from).
- A Render account (https://render.com — free tier is enough for a POC).
- A Vercel account (https://vercel.com — free tier is enough for a POC).
- Your Groq API key (already in `backend/.env` locally — never commit that file).

## 1. Push the repo to GitHub

Local git is already initialized and the first commit made. Create an empty
repo on GitHub (no README/license — this repo already has one), then:

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

## 2. Deploy the backend to Render

1. Render dashboard → **New** → **Blueprint** → connect the GitHub repo you
   just pushed. Render will detect `render.yaml` at the repo root and
   propose one service: `catalyst-advisor-backend`.
2. Before the first deploy, set the one secret `render.yaml` deliberately
   leaves blank (`sync: false`): **GROQ_API_KEY** — paste the value from
   `backend/.env`.
3. Deploy. Render builds with `pip install -r requirements.txt` (from
   `backend/`) and starts with `uvicorn app.main:app --host 0.0.0.0 --port
   $PORT`. Health check is `/health`.
4. Once live, note the service URL — something like
   `https://catalyst-advisor-backend.onrender.com`. Confirm it works:
   ```bash
   curl https://catalyst-advisor-backend.onrender.com/health
   ```
   Expect `{"status":"ok"}`.

**Free-tier note:** Render's free web services spin down after 15 minutes
idle and take 30-60s to wake on the next request — the demo's first request
after a quiet period will be slow. Fine for a POC; upgrade the plan if that
matters for a live demo.

## 3. Deploy the frontend to Vercel

1. Vercel dashboard → **Add New** → **Project** → import the same GitHub
   repo.
2. **Root Directory**: set to `frontend` (this is a monorepo — Vercel needs
   to know the app doesn't live at the repo root). Framework preset should
   auto-detect as Vite once the root directory is set.
3. Add an environment variable: **`VITE_API_BASE_URL`** = the Render URL
   from step 2.4 (no trailing slash), e.g.
   `https://catalyst-advisor-backend.onrender.com`.
4. Deploy. Vercel builds with `npm run build` and serves `dist/`;
   `frontend/vercel.json` handles client-side routing so refreshing
   `/report` doesn't 404.
5. Note the resulting domain, e.g. `https://catalyst-advisor.vercel.app`.

## 4. Close the loop: CORS

The backend's `FRONTEND_ORIGIN` env var currently points at a placeholder.
Back in the Render dashboard, update it to the real Vercel domain from step
3.5, then trigger a redeploy (Render redeploys automatically on an env var
change). Without this, the deployed frontend's requests will be blocked by
CORS.

## 5. Verify end-to-end

Open the Vercel URL, submit an idea, confirm a report comes back. Check the
Render service logs for the request — you should see the Groq API call
(or, if `GROQ_API_KEY` is wrong/missing, a `MockLLMProvider` fallback
warning — still a valid report, just not real Groq output).

## Notes

- **No database, no persistence** — every request is scored fresh and
  returned. Nothing to migrate or back up.
- **Secrets** live only in Render's dashboard and your local `backend/.env`
  (gitignored) — never in the repo.
- **Updating the deploy**: push to `main`; both Render and Vercel redeploy
  automatically from the GitHub connection.
- **Preview deployments**: Vercel gives every branch/PR its own preview
  URL, which won't match `FRONTEND_ORIGIN` and will get CORS-blocked by the
  backend. Fine for a POC (the production URL is what matters); if preview
  deploys need to hit the API too, make `FRONTEND_ORIGIN` a comma-separated
  list (already supported by `backend/app/main.py`).
