# O.T. 012 — Validation report

## Automated validation

- Backend and contract tests: **63 passed**.
- Frontend tests: **4 passed**.
- Acceptance matrix: **68 cases**.
- TypeScript and Vite production build: **OK**.
- Isolated Python installation and `pip check`: **OK**.
- Production npm vulnerabilities: **0**.

## End-to-end result

```text
Import: 33 chats
Deterministic analysis: 45 findings
Semantic reconstruction: 7 projects
Proposals: 20
Preview: 7 projects
Application: APPLIED
Undo: COMPLETED
Restored hash equals before hash: true
```

The full reviewed route records nine audit events: proposal creation, safe-batch approval, four exception decisions, preview, application and Undo.

## Integrity

- Source SHA-256 manifest unchanged.
- `originals_modified` remains false in preview, application and Undo responses.
- Partial duplicates are recorded but never merged automatically.
- Rejected or unresolved items are not applied.
