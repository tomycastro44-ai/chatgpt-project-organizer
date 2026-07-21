# Architecture

## Overview

ChatGPT Project Organizer is a local-first demonstration application with a React/TypeScript frontend, a FastAPI backend and SQLite persistence.

```text
React UI
   ↓ /api/v1
FastAPI routes
   ↓
Application services
   ├── immutable import storage and normalization
   ├── deterministic analysis and evidence
   ├── semantic project reconstruction
   ├── proposal and human review workflow
   └── simulated workspace, audit and Undo
   ↓
SQLAlchemy + SQLite
```

## Data layers

1. **Original sources** — copied into protected runtime storage and never edited.
2. **Normalized data** — common `Chat` and `Message` representation.
3. **Deterministic analysis** — reproducible findings and linked evidence.
4. **Semantic memory** — projects, memberships, project state and exceptions.
5. **Proposals** — operations awaiting user authorization.
6. **Simulated workspace** — derived organized state only.
7. **Audit and Undo** — before/after snapshots and ordered events.

## Deterministic and semantic split

Deterministic logic owns integrity, chronology, exact duplication, state hashes, application and Undo. Semantic reconstruction uses the OpenAI Responses API in LIVE mode and Structured Outputs validated by Pydantic. The included DEMO mode uses approved precomputed results and is explicitly labeled as such.

## Reversibility

The application calculates canonical SHA-256 hashes for workspace states. Apply stores the exact before and after JSON snapshots. Undo succeeds only when the current workspace hash still matches the applied operation, preventing unsafe restoration over an unrelated state.

## API boundary

All endpoints are versioned under `/api/v1`. The OpenAI key is read only by the backend and is never included in frontend source, API responses, screenshots or logs.
