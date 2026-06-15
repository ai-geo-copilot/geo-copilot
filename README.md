# GEO Copilot

API-based GEO Copilot for single-URL page evidence, GEO method retrieval, DeepSeek JSON diagnosis, and report follow-up.

## Local Development

API:

```bash
python -m venv .venv
.venv\Scripts\pip install -r apps/api/requirements.txt
python -m uvicorn apps.api.app.main:app --reload --port 8000
```

Web:

```bash
npm install
npm --workspace apps/web run dev
```

Default URLs:

- API: http://localhost:8000
- OpenAPI: http://localhost:8000/openapi.json
- Web: http://localhost:3000

## Scope

This scaffold implements Sprint 0 foundations only: monorepo layout, stable placeholder API contracts, shared JSON schemas, initial migrations, Docker compose, and a minimal frontend calling the API health endpoint.

## Development Status

The single source of truth for current development status is `docs/DEVELOPMENT_STATUS.md`.

## Project Documents

The single entry point for project design documents is `docs/README.md`.
