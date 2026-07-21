# O.T. 008 — Technical repository and runtime foundation

## Status

- Phase: **FASE 4 — CONSTRUCTION**
- Work order: **O.T. 008**
- Deliverable status: **EN_REVISION**
- Version: **OT008-v1**
- Approved inputs: **O.T. 006** and **O.T. 007**

## Objective

Create the first executable and reproducible repository baseline without advancing into domain functionality.

## Implemented

### Repository

- Required public-repository structure.
- MIT license.
- `.gitignore` and `.env.example`.
- Windows and Unix scripts.
- Immutable data manifest.

### Backend

- FastAPI application factory.
- Versioned `/api/v1` router.
- Health and system endpoints.
- Read-only approved dataset summary endpoint.
- SQLAlchemy engine and SQLite initialization.
- Minimal `schema_metadata` table only.
- Strict Pydantic response contracts.
- CORS restricted to configured origins.

### Frontend

- React and TypeScript application.
- Vite development and build configuration.
- Approved visual language from O.T. 007.
- Backend health and demo summary integration.
- Responsive technical-foundation screen.
- Unit test with mocked API responses.

### Validation

- Backend pytest suite.
- Frontend Vitest suite.
- Production frontend build.
- Repository contract validation.
- SHA-256 verification of approved source files.

## Deliberately excluded

- domain entities from the final data model;
- import services;
- OpenAI client;
- GPT-5.6 prompts or calls;
- semantic analysis;
- proposal generation;
- user review persistence;
- apply, audit, and undo operations;
- authentication and multiuser support.

## Technical boundary

O.T. 008 establishes infrastructure only. Later work orders must extend this repository rather than create a parallel implementation.

## Acceptance criteria

The work order is ready for approval when:

1. setup scripts complete on a clean environment;
2. backend tests pass;
3. frontend tests pass;
4. frontend production build succeeds;
5. repository validator returns `OT-008 VALIDATION: OK`;
6. approved O.T. 006 source hashes remain unchanged;
7. no API key or private data exists in the package;
8. the repository can start frontend and backend locally;
9. no domain functionality outside the work order has been introduced.
