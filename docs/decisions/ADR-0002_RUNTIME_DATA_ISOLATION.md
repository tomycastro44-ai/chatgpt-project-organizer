# ADR-0002 — Runtime data isolation

## Status

Accepted for O.T. 008 review.

## Decision

Approved imported source files remain under `demo-data/source` and are protected by SHA-256 hashes. Runtime SQLite data is stored under `data/` and excluded from version control.

## Consequences

- Source files cannot be confused with derived state.
- Local tests and runtime operations cannot overwrite approved fixtures.
- Future apply and undo operations must work only on derived database records.
