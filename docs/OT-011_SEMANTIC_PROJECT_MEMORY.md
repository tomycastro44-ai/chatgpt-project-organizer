# O.T. 011 — Semantic project reconstruction and operational memory

## State

`EN_REVISION`

## Objective

Transform the normalized conversations and deterministic evidence into project groups and reversible operational memories. The O.T. integrates the public OpenAI Responses API for live analysis and preserves an explicitly labelled reproducible demo mode.

## Implemented

- Semantic run history linked to an approved deterministic analysis.
- `Project`, `ProjectMembership`, `ProjectEvidence` and `SemanticException` persistence.
- OpenAI Responses API provider using `gpt-5.6` and Pydantic Structured Outputs.
- Server-side API key only.
- Approved demo provider based on O.T. 006 fixtures.
- Strict output validation before persistence.
- Project lifecycle state, current/previous/discarded versions, phase, decisions, tasks, blockers, latest advance and next step.
- Confirmed and doubtful memberships.
- Evidence traceability to external chat/message IDs.
- Independent and unclassified chat lists.
- Responsive React project-memory workspace.
- Explicit visual distinction between `DEMO · PRECOMPUTED` and `LIVE · OPENAI RESPONSES API`.

## API

```text
GET  /api/v1/semantic-runs/capabilities
POST /api/v1/semantic-runs
GET  /api/v1/semantic-runs
GET  /api/v1/semantic-runs/{run_id}
```

Create request:

```json
{
  "analysis_run_id": "uuid",
  "mode": "DEMO"
}
```

## Reproducible canonical result

- 7 projects.
- 5 lifecycle states represented.
- 4 review exceptions.
- 4 independent chats.
- 1 unclassified chat.
- Exact duplicate copy excluded from project memberships.
- StockCore remains `ACTIVO` because the latest explicit decision overrides the old closure suggestion.

## Live mode

Live mode calls the official OpenAI Responses API using:

- model alias `gpt-5.6`;
- `client.responses.parse`;
- Pydantic output model `SemanticAnalysisPayload`;
- reasoning effort configured by environment;
- `store=false`;
- API key available only to the backend.

## Boundaries

Not implemented in this O.T.:

- proposal generation;
- user correction/rejection persistence;
- simulated application;
- application audit;
- Undo.

No source file or original normalized conversation is modified.
