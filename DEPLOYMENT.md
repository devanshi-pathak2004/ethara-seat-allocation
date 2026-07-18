# Deployment Notes

The app is designed to deploy as **two services**: a FastAPI backend and a
static React frontend. Below are the recommended, tested paths.

---

## Recommended: Render (backend) + Vercel (frontend)

### 1. Backend → Render

This repo ships a **`render.yaml`** blueprint.

**Option A — Blueprint (one click):**
1. Push this repo to GitHub.
2. Render dashboard → **New + → Blueprint** → select the repo.
3. Render reads `render.yaml`, builds `backend/`, seeds the DB if empty, and
   starts uvicorn. Note the service URL, e.g. `https://ethara-seat-api.onrender.com`.

**Option B — Manual web service:**
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command:
  `python -m app.seed_if_empty && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment: `CORS_ORIGINS=*` (or your frontend URL), `PYTHON_VERSION=3.12.7`

> **Persistence:** SQLite lives on the container's ephemeral disk, which is fine
> for a demo (it re-seeds on a fresh deploy). For durable data, add a Render
> **PostgreSQL** instance and set `DATABASE_URL` — the code auto-switches and
> even rewrites `postgres://` → `postgresql://`.

Verify: open `https://<backend>/docs`.

### 2. Frontend → Vercel

1. Vercel → **New Project** → import the repo.
2. **Root directory:** `frontend`
3. Framework preset: **Vite** (build `npm run build`, output `dist`).
4. **Environment variable:** `VITE_API_URL = https://<your-backend-url>`
5. Deploy. `vercel.json` provides the SPA rewrite so deep links work.

> `VITE_API_URL` is baked in at **build time**, so redeploy the frontend if the
> backend URL changes.

---

## Alternative: Netlify (frontend)

- Base directory: `frontend`
- Build command: `npm run build`, publish directory: `frontend/dist`
- Env var: `VITE_API_URL=https://<your-backend-url>`
- `netlify.toml` already includes the SPA redirect.

## Alternative: Railway (backend)

- New project → Deploy from repo → set root to `backend`.
- Start command: `python -m app.seed_if_empty && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Add a PostgreSQL plugin and Railway injects `DATABASE_URL` automatically.

---

## Docker (self-hosted / any VM)

Whole stack in one command:

```bash
docker compose up --build
# frontend → http://localhost:5173   backend → http://localhost:8000/docs
```

- `backend/Dockerfile` — Python 3.12-slim, seeds if empty, serves uvicorn.
- `frontend/Dockerfile` — multi-stage build → nginx with SPA fallback. Pass the
  backend URL via the `VITE_API_URL` build arg.

---

## Post-deploy checklist

- [ ] `GET /health` on the backend returns `{"status":"healthy"}`.
- [ ] `/docs` (Swagger) loads.
- [ ] Frontend dashboard renders numbers (confirms CORS + `VITE_API_URL`).
- [ ] AI assistant answers *"Where is my seat? My email is amit@ethara.ai"*.
- [ ] `CORS_ORIGINS` set to the frontend origin (tighten from `*` for production).

## Submission URLs (fill in after deploying)

| Item | URL |
|------|-----|
| Live frontend | `https://…` |
| Live backend | `https://…` |
| Swagger / API docs | `https://…/docs` |
| GitHub repository | `https://github.com/…` |
