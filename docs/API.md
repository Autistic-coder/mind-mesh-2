# API guide

Interactive OpenAPI documentation is available at `/docs` on the backend.

## Public endpoints

- `GET /api/health`: process liveness.
- `GET /api/ready`: database and model readiness.
- `POST /api/auth/register`, `POST /api/auth/login`: session creation.

## Authenticated endpoints

- `GET /api/auth/me`, `GET /api/auth/csrf`, `POST /api/auth/logout`.
- `GET|POST /api/predictions`, `GET|DELETE /api/predictions/{id}`.
- `GET /api/batches/template`, `POST /api/batches`, `GET /api/batches/{id}/download`.
- `GET /api/model-report`, `GET /api/overview`.
- `GET|POST /api/conversations`.
- `PATCH /api/account`.

State-changing endpoints require the HttpOnly session cookie and `X-CSRF-Token`. The browser obtains the latter from `/api/auth/csrf`. Never send a user ID; it is ignored as an ownership mechanism.

Machine input JSON uses the exact six model feature names. Invalid units, ranges, missing columns and unexpected machine types return 422 responses. Batch CSV headers must exactly match the downloadable template.

