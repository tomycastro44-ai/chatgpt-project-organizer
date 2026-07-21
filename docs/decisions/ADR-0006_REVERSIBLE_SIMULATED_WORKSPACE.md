# ADR-0006 — Reversible simulated workspace

## Decision

Approved proposals update only a derived `WorkspaceState`. Original imports, normalized chats, deterministic findings and semantic memory remain immutable.

Every application stores canonical JSON snapshots and SHA-256 hashes for the state before and after the operation. Undo is permitted only when the current state still matches the stored after-hash.

## Consequences

- preview and application are deterministic;
- stale or conflicting Undo operations are rejected;
- audit history is preserved after restoration;
- no source chat is moved, renamed, archived or deleted;
- later native integrations can translate the same operation contract without changing the MVP integrity model.
