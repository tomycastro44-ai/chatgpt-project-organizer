# ADR-0003 — Import isolation and normalization

## Decision

Each import creates an immutable copy of every accepted source in `data/imports/<batch>/originals`, records its SHA-256 digest, parses it through a format-specific adapter and persists a common Chat/Message representation in SQLite.

## Consequences

- Original approved fixtures and user-selected source files are never edited.
- Invalid files or records create structured issues and do not roll back valid files in the same batch.
- Internal UUIDs prevent collisions between repeated imports; external IDs remain searchable evidence.
- Semantic analysis remains outside O.T. 009.
