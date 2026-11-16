# Troubleshooting

## API readiness returns 503

Check that model and manifest paths exist and `DATABASE_URL` uses `postgresql+psycopg://` with `sslmode=require`. Run `python -m alembic -c alembic.ini current` from `backend`.

## Login succeeds but later requests are 401/403

In production confirm `SECURE_COOKIES=true`, the cookie is `SameSite=None; Secure`, `FRONTEND_ORIGINS` exactly equals the browser origin and `VITE_API_URL` uses HTTPS. A 403 indicates the CSRF endpoint/header flow failed; inspect network requests without copying token values.

## CORS error

Do not add `*`. Correct the exact origin string, including scheme and excluding a trailing path. Render environment changes require a deploy before they are active.

## Model schema mismatch

Do not hand-edit the manifest. Retrain intentionally from the validated raw CSV and keep the joblib artifact and generated manifest from the same run.

## Batch rejected

Use the downloaded UTF-8 template, preserve header spelling/order, keep 1–500 data rows and observe ranges shown on New Prediction.

## Vercel route returns 404 after refresh

Confirm `frontend/vercel.json` is active and the Vercel project Root Directory is `frontend`; the SPA rewrite must point all routes to `/index.html`.

## Render build or startup fails

Inspect the first failing lifecycle stage. Confirm Python 3.11, requirements installation, port binding to `0.0.0.0:$PORT`, environment keys, Neon reachability and `/api/ready`. Fix the first cause before redeploying.
