# Architecture and security

## Components

The Vite single-page application is a presentation client. FastAPI is the security boundary and owns validation, authentication, inference, persistence, exports and assistant-provider access. Neon PostgreSQL persists application records. A versioned joblib artifact contains the complete preprocessing/model pipeline and is deployed with the API.

## Request flow

1. Registration or login verifies an Argon2id password and creates a random session token.
2. Only a SHA-256 digest of that token is stored in PostgreSQL; the raw token is an HttpOnly cookie.
3. In production the cookie is `Secure; SameSite=None`, required because Vercel and Render use different sites.
4. The browser fetches a CSRF token through the credentialed `/api/auth/csrf` endpoint and returns it in `X-CSRF-Token` for state changes.
5. The API derives the user from the session and includes `user_id` in every ownership query.
6. Validated inputs become the six-column DataFrame schema and pass through the loaded pipeline under a process lock.
7. Results and the model version are committed in one database transaction.

## Data model

- `users`: profile and Argon2id hash.
- `sessions`: hashed token ID, CSRF token, owner and expiry.
- `predictions`: owner, optional batch, inputs, probability, classification, risk and model version.
- `batch_jobs`: owner, safe filename metadata and row count.
- `conversations`: private user/assistant messages and optional explicitly shared prediction summary.
- `model_versions`: training evidence for database-backed release tracking.

## Boundaries and controls

- Exact CORS allow-list with credentials; no wildcard origins.
- Server-side Pydantic ranges and strict machine types.
- 1 MB uploads and 500 batch rows maximum.
- CSV export formula prefixes are neutralised.
- Generic login errors and bounded login, registration, prediction and chat rates.
- No user-uploaded model deserialisation.
- Secrets are runtime environment values only.
- `/api/health` is liveness; `/api/ready` checks database and model.

The current rate limiter is process-local for one Render instance. Replace it with a shared store before horizontal scaling.

