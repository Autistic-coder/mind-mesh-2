# MindMesh 2

MindMesh 2 is a production-oriented predictive-maintenance application that estimates whether an industrial machine is at risk of failure. It uses one fixed Random Forest classifier trained on the AI4I 2020 Predictive Maintenance Dataset and exposes that saved pipeline through a secure FastAPI service and an accessible React application.

The result supports maintenance prioritisation; it is not a diagnosis and never replaces qualified inspection.

## Verified model result

The training script selected a `0.36` probability threshold using validation data only and evaluated it once on the untouched 1,500-row test set.

| Measure | Actual result |
| --- | ---: |
| Accuracy | 0.9780 |
| Precision | 0.6607 |
| Failure recall | 0.7255 |
| F1 | 0.6916 |
| ROC–AUC | 0.9768 |
| Confusion matrix | `[[1430, 19], [14, 37]]` |
| False negatives | 14 |
| Always-normal baseline accuracy | 0.9660 (recall 0) |

Accuracy alone is misleading because only 339 of 10,000 dataset records are failures. Failure recall and the 14 missed failures are therefore emphasised throughout the product.

## Architecture

```text
React + TypeScript (Vercel)
        │ HTTPS, exact CORS, credentialed cookies, CSRF
        ▼
FastAPI (Render) ── saved joblib Pipeline + manifest
        │
        ├── Neon PostgreSQL (users, sessions, predictions, batches, conversations)
        └── OpenAI API (optional, explicit prediction-summary consent only)
```

- The browser never supplies or selects an account ID for ownership.
- The API resolves ownership from a hashed server-managed session.
- The model pipeline loads once per process and never retrains on API startup.
- Alembic owns the persistent schema; Render runs migrations before starting the API.
- Raw data, ZIP archives, environment files and user records are not committed.

See [Architecture](docs/ARCHITECTURE.md), [API](docs/API.md), and [Deployment](docs/DEPLOYMENT.md).

## Model and data

Inputs are `Type`, air temperature, process temperature, rotational speed, torque, and tool wear. `UDI`/`UID` and Product ID are identifiers; `TWF`, `HDF`, `PWF`, `OSF`, and `RNF` leak failure outcomes and are excluded. The categorical Type column is encoded inside a scikit-learn `ColumnTransformer`; preprocessing and the Random Forest are saved together.

The manifest records the dataset SHA-256, feature schema, split sizes, seed, estimator settings, validation threshold, test metrics and library versions. See [Model training](docs/MODEL.md).

## Local setup — Windows PowerShell

From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\backend\requirements-dev.txt

New-Item -ItemType Directory -Force -Path .\data\raw | Out-Null
Expand-Archive -LiteralPath .\ai4i+2020+predictive+maintenance+dataset.zip -DestinationPath .\data\raw

# Intentional reproducible retraining (not run by the API)
python .\model\train.py --data .\data\raw\ai4i2020.csv --output .\model

$env:DATABASE_URL = 'postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require'
$env:FRONTEND_ORIGINS = 'http://localhost:5173'
$env:SECURE_COOKIES = 'false'

Set-Location .\backend
python -m alembic -c alembic.ini upgrade head
Set-Location ..
python -m uvicorn backend.app.main:app --reload --port 8000
```

In a second PowerShell window:

```powershell
Set-Location .\frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`. API documentation is at `http://localhost:8000/docs`.

## Tests and quality checks

```powershell
python -m ruff format --check backend model
python -m ruff check backend model
python -m pytest -q

Set-Location .\frontend
npm run typecheck
npm run lint
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

Current verified counts: 18 backend tests, 5 React component tests, and 2 Chromium end-to-end tests.

## Environment variables

| Variable | Where | Required | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | API | Yes | Neon pooled PostgreSQL URL using `postgresql+psycopg://` and TLS |
| `FRONTEND_ORIGINS` | API | Yes | Exact comma-separated browser origins |
| `SECURE_COOKIES` | API | Production | Enables Secure, cross-site session cookies |
| `MODEL_PATH` | API | Default supplied | Saved joblib pipeline path |
| `MODEL_MANIFEST_PATH` | API | Default supplied | Manifest path |
| `OPENAI_API_KEY` | API | No | Enables AI answers; absent means labelled static help |
| `OPENAI_MODEL` | API | No | Configurable OpenAI model name |
| `VITE_API_URL` | Frontend build | Yes | Public Render API origin |

Use the committed `.env.example` files as key references only. Never commit real `.env` files.

## Deployment

- GitHub: `https://github.com/Autistic-coder/mind-mesh-2`
- Vercel project: `mindmesh2`, root directory `frontend`
- Render Blueprint service: `mindmesh2-api`
- Database: Neon PostgreSQL, migrated with `python -m alembic -c alembic.ini upgrade head`

Follow [Deployment and Neon migrations](docs/DEPLOYMENT.md). The `render.yaml` Blueprint uses the smallest current Render web-service plan, exact readiness checks, automatic main-branch deploys, and secret prompts rather than committed values.

## Limitations

- AI4I is synthetic and may not represent a specific factory or machine population.
- Failure examples are rare; the model still misses 14 of 51 failures in the test split.
- The fixed accepted ranges are dataset-derived and not universal safe-operating limits.
- Feature importance is associative, not causal.
- The in-process rate limiter is per API instance; a shared limiter is recommended if the API scales horizontally.
- Static help remains available when no OpenAI key is configured.

## Teaching materials

- [Teacher demonstration](docs/TEACHER_DEMO.md)
- [Viva questions and short answers](docs/VIVA.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Dataset source

The dataset is the [AI4I 2020 Predictive Maintenance Dataset](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset) from the UCI Machine Learning Repository. Review its source terms before redistributing raw data. This repository intentionally excludes the supplied archive and extracted CSV.
