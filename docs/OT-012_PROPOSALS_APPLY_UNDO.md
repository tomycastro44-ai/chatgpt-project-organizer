# O.T. 012 — Proposals, review, simulated application, audit and Undo

## Status

`EN_REVISION`

## Objective

Complete the central MVP workflow after semantic reconstruction: generate a global proposal, approve safe operations as one batch, review exceptions, preview the complete result, apply only authorized operations to a derived workspace, audit every decision and restore the exact previous state.

## Implemented entities

- `ProposalRun`
- `ProposalItem`
- `UserReview`
- `WorkspaceState`
- `AppliedOperation`
- `UndoOperation`
- `AuditEvent`

## API

```text
POST /api/v1/proposal-runs
GET  /api/v1/proposal-runs
GET  /api/v1/proposal-runs/{run_id}
POST /api/v1/proposal-runs/{run_id}/approve-safe
POST /api/v1/proposal-runs/{run_id}/items/{item_id}/review
POST /api/v1/proposal-runs/{run_id}/preview
POST /api/v1/proposal-runs/{run_id}/apply
GET  /api/v1/proposal-runs/{run_id}/audit
POST /api/v1/applied-operations/{operation_id}/undo
```

## Canonical demo result

- 20 proposals;
- 16 safe operations;
- 4 exceptions;
- 7 organized projects after full review;
- 1 exact duplicate relation;
- 1 partial duplicate relation without merge;
- 4 independent chats;
- 2 unclassified chats after the approved review decisions;
- 0 original files or conversations modified.

## Review decisions used by the demo

- `P-017`: reject classification; keep `CHAT-029` unclassified.
- `P-018`: correct and assign `CHAT-014` to `PRJ-SCANLINK`.
- `P-019`: reject membership; keep `CHAT-031` unclassified.
- `P-020`: approve partial-duplicate relation without merging.

## Integrity model

Preview computes a canonical proposed state without changing persistence. Apply stores both state snapshots and their hashes. Undo restores the exact before-state only when the current workspace hash still matches the applied after-state. Audit events are never deleted.

## Scope boundary

The O.T. does not modify real ChatGPT data. All organization operations are simulated and reversible. Authentication, multiuser access and private ChatGPT APIs remain outside the MVP.
