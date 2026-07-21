# O.T. 013 — Integrated validation and technical release

## Status

- Phase: **FASE 5 — VALIDATION**
- Work order: **O.T. 013**
- Status: **EN_REVISION**
- Version: **OT013-v1**
- Approved base: **OT012-v1**

## Objective

Validate the complete MVP as one integrated system and prepare a clean technical release that can be installed, tested and demonstrated without reconstructing previous work orders.

## Scope completed

- clean Python and npm installation;
- complete backend and repository-contract test suite;
- frontend component tests;
- TypeScript and Vite production build;
- full public-API demonstration from import through exact Undo;
- two isolated deterministic demo executions;
- runtime backend and frontend startup;
- frontend proxy validation;
- dependency consistency and production npm audit;
- Python bytecode compilation;
- original-source integrity verification;
- secret and API-key scan;
- OpenAPI endpoint contract validation;
- final architecture, security, testing, demonstration and limitation documentation;
- clean release packaging without dependencies or runtime data.

## Canonical integrated result

| Metric | Result |
|---|---:|
| Imported source files | 3 |
| Chats | 33 |
| Messages | 51 |
| Deterministic findings | 45 |
| Evidence records | 61 |
| Projects | 7 |
| Memberships | 29 |
| Semantic exceptions | 4 |
| Proposals | 20 |
| Safe proposals | 16 |
| Review exceptions | 4 |
| Audit events | 9 |
| Original modifications | 0 |

## Correction applied

The existing repository contract treated any runtime SQLite file created after application startup as if it had been committed to the source package. This was a false positive.

The localized correction now verifies:

- runtime database patterns are present in `.gitignore`;
- no database file is listed in the release manifest.

No application behavior, database model, API or approved workflow changed.

## Acceptance

O.T. 013 may be approved when:

- all 63 backend and repository-contract tests pass;
- all 4 frontend tests pass;
- the production build succeeds;
- all 50 O.T. 013 acceptance cases pass;
- two isolated demo flows produce the same normalized result;
- apply and Undo preserve exact state hashes;
- original source hashes remain unchanged;
- the clean ZIP can be installed and validated independently;
- no secret or runtime database is present in the release package.
