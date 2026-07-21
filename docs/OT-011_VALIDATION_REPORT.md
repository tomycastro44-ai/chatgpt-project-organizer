# O.T. 011 — Validation report

## Functional validation

- Approved demo import: `33` chats and `51` messages.
- Deterministic analysis: `45` findings and `61` evidences.
- Semantic reconstruction: `7` projects and `4` review exceptions.
- Required states: `ACTIVO`, `PENDIENTE`, `EN_PAUSA`, `CERRADO`, `ARCHIVADO`.
- Exact duplicate `CHAT-004` is not assigned as a separate project membership.
- Operational memories include versions, decisions, tasks, blockers, evidence and next step.
- Demo output is explicitly identified as precomputed.
- Live mode is unavailable without `OPENAI_API_KEY` and returns a controlled conflict response.
- Mocked structured live output is validated and persisted.
- Repeated runs retain independent history and the same input digest.

## Technical validation

- Python source compilation: OK.
- Backend and repository tests: `52` passed.
- Frontend tests: `4` passed.
- TypeScript production build: OK.
- Clean Python virtual environment installation: OK.
- OpenAI SDK version: `2.46.0`.
- `responses.parse` contract inspected: OK.
- `pip check`: OK.
- npm production vulnerability audit: 0 vulnerabilities.
- Runtime API import → deterministic analysis → semantic demo: OK (`7` projects, `29` memberships, `4` exceptions).
- SQLite foreign keys: enabled.
- Original demo-source SHA-256: unchanged.
- API key not present in frontend or persisted data: verified.

## Result

`OT-011 VALIDATION: OK`
