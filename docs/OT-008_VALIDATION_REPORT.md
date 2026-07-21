# O.T. 008 — Validation report

Date: 2026-07-20  
Version: `OT008-v1`  
Status: `EN_REVISION`

## Clean installation

- Python virtual environment created from `backend/requirements.txt`.
- Frontend dependencies installed using `npm ci` and `package-lock.json`.
- `pip check`: no broken requirements.
- `npm audit --omit=dev --audit-level=high`: 0 vulnerabilities.

## Automated validation

```text
Backend and repository tests: 6 passed
Frontend tests: 1 passed
Frontend production build: passed
OT-008 VALIDATION: OK
Repository structure: OK
Approved dataset integrity: OK
Secret handling: OK
Frontend architecture: React + TypeScript
Backend architecture: FastAPI + SQLAlchemy + SQLite
```

## Runtime smoke test

- FastAPI started on a temporary SQLite database.
- `GET /api/v1/health`: `200 OK`.
- `GET /api/v1/system`: validated.
- `GET /api/v1/demo/summary`: validated against O.T. 006 counts.
- Vite production preview started.
- Frontend HTML title validated.

## Integrity

- Approved O.T. 006 source files match the SHA-256 immutability manifest.
- No source file was modified by tests or runtime smoke checks.
- No API key exists in the package.
- Runtime database files are excluded.

## Scope control

No semantic analysis, OpenAI API integration, domain operation, proposal application, audit, or undo logic was implemented.
