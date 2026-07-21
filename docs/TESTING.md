# Testing and validation

## Standard validation

```bash
./scripts/setup.sh
./scripts/release-check.sh
```

Windows PowerShell:

```powershell
.\scripts\setup.ps1
.\scripts\release-check.ps1
```

## Test layers

- **Backend tests:** API behavior, persistence, import isolation, deterministic analysis, semantic contracts, proposals, apply, audit and Undo.
- **Repository contracts:** required files, architecture boundaries and source integrity.
- **Frontend tests:** loading, navigation and core workflow states.
- **Production build:** TypeScript compilation and Vite bundle.
- **Release validator:** end-to-end demo flow using an isolated SQLite database.
- **Dependency checks:** `pip check` and production `npm audit`.

## Expected canonical result

| Metric | Expected |
|---|---:|
| Imported chats | 33 |
| Imported messages | 51 |
| Deterministic findings | 45 |
| Evidence records | 61 |
| Semantic projects | 7 |
| Proposal items | 20 |
| Safe proposals | 16 |
| Exceptions | 4 |
| Audit events | 9 |
| Original modifications | 0 |

Undo must restore the exact pre-apply hash while retaining the audit history.
