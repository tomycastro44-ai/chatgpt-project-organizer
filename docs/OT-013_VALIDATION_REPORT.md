# O.T. 013 validation report

## Result

**OT-013 VALIDATION: OK**

## Automated validation

| Validation | Result |
|---|---|
| Backend and repository contracts | 63 passed |
| Frontend tests | 4 passed |
| O.T. 013 acceptance matrix | 50 passed |
| TypeScript compilation | OK |
| Vite production build | OK |
| Python compileall | OK |
| `pip check` | OK |
| Production `npm audit` | 0 vulnerabilities |
| Secret scan | OK |
| Original-source SHA-256 | OK |
| OpenAPI required endpoints | OK |
| Two isolated full demo executions | OK |
| Runtime backend startup | OK |
| Runtime frontend startup | OK |
| Frontend API proxy | OK |

## Complete workflow verified

```text
Import 3 files
→ 33 chats / 51 messages
→ 45 deterministic findings / 61 evidence records
→ 7 semantic projects / 4 exceptions
→ 20 proposals / 16 safe
→ human review of 4 exceptions
→ before/after preview
→ simulated apply
→ 9 ordered audit events
→ exact Undo
```

## Reversibility result

- apply status: `APPLIED`;
- originals modified: `false`;
- Undo status: `COMPLETED`;
- restored hash equals before hash: `true`;
- audit history preserved: `true`.

## Runtime demonstration result

The public API flow completed successfully against a running FastAPI process. The detailed machine-readable output is stored in `docs/OT-013_RUNTIME_DEMO_RESULT.json`.

## Live OpenAI boundary

The release validates the official SDK contract, Responses API integration, Pydantic Structured Outputs, backend-only key handling and `store=false`. A real LIVE call is not part of this validation because no API key is stored in the release environment. DEMO mode is fully functional and explicitly labeled as precomputed.

## Known non-blocking limitations

See `docs/LIMITATIONS.md`. No critical defect remains in the local demonstration workflow.
