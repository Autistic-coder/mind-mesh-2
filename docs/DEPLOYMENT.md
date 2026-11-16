# Deployment and Neon migrations

## 1. Neon PostgreSQL

Create a Neon project close to the Render region. Copy its pooled connection string into a secret manager and change only the SQLAlchemy scheme from `postgresql://` to `postgresql+psycopg://`. Keep `sslmode=require`. Never paste the URL into source, `render.yaml`, logs or screenshots.

Test migrations locally against a non-production branch/database:

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require'
Set-Location .\backend
python -m alembic -c alembic.ini current
python -m alembic -c alembic.ini upgrade head
python -m alembic -c alembic.ini current
```

The Render start script applies idempotent Alembic upgrades before starting Uvicorn. For a larger production service, move migrations to Render's paid pre-deploy command so migrations run once outside the web instance lifecycle. Downgrades can lose data and must not be run casually.

## 2. Render API

`render.yaml` defines one Python web service named `mindmesh2-api`, a free plan, main-branch automatic deploys, a `/api/ready` health check and one worker process. Apply the Blueprint from:

`https://dashboard.render.com/blueprint/new?repo=https://github.com/Autistic-coder/mind-mesh-2`

Provide these secret/manual values during initial creation:

- `DATABASE_URL`: Neon pooled URL using `postgresql+psycopg://`.
- `FRONTEND_ORIGINS`: exact final Vercel origin, such as `https://mindmesh2.vercel.app`.
- `OPENAI_API_KEY`: optional; leave empty for labelled static help.

After the deploy reaches `live`, verify `/api/health`, `/api/ready`, recent error logs, the deployed commit and the migration revision.

## 3. Vercel frontend

Create/link project `mindmesh2` to the GitHub repository with Root Directory `frontend`. Add `VITE_API_URL` in Production and Preview environments with the exact Render origin (no trailing slash). The committed `frontend/vercel.json` builds Vite, serves `dist`, preserves client-side routing and adds defensive headers.

Vercel's Git integration deploys main to production automatically. Verify the selected team/project/commit before promotion. A release is not complete until registration, prediction, history, logout and account isolation work against Render and Neon.

## 4. Cross-origin checklist

- API `SECURE_COOKIES=true`.
- API `FRONTEND_ORIGINS` exactly matches the deployed frontend.
- Frontend `VITE_API_URL` exactly matches the API.
- Requests include credentials.
- Session cookie shows Secure, HttpOnly and SameSite=None.
- No wildcard CORS origin is used.

