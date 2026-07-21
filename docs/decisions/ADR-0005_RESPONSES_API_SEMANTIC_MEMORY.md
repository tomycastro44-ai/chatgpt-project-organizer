# ADR-0005 — Responses API semantic reconstruction and explicit demo mode

## Decision

Use a provider boundary with two modes:

- `LIVE`: OpenAI Responses API, model alias `gpt-5.6`, Pydantic structured output and `store=false`.
- `DEMO`: frozen O.T. 006 expected output, clearly labelled as precomputed and never represented as a live model call.

Deterministic findings from O.T. 010 are passed as evidence and constraints. Semantic output is validated before persistence. Unknown chat/message identifiers, duplicate project keys, dual confirmed memberships and exact-duplicate memberships are rejected.

## Security

`OPENAI_API_KEY` is read only by the backend from the environment. It is not returned by the API, persisted in SQLite, included in logs, sent to the frontend or packaged in the repository.

## Consequences

The demo remains reproducible without network access. Live evaluation can use the public OpenAI API without changing the data model or frontend flow.
