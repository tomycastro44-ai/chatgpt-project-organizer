# ChatGPT Project Organizer

> Turn months of scattered AI conversations into structured, evidence-backed and reversible projects.

ChatGPT Project Organizer is a local-first prototype that imports exported conversations, detects objective evidence, reconstructs project context with GPT-5.6, generates a global organization proposal, asks the user to review only ambiguous cases, previews the result, applies approved changes to a simulated workspace, and supports exact Undo.

**Original files and conversations are never modified.**

## Why this exists

Long-running AI users accumulate hundreds of conversations containing active projects, obsolete versions, repeated decisions, forgotten tasks and unrelated one-off questions. Manual organization requires rereading every chat and still risks losing the most recent decision.

This project treats conversation history as operational knowledge rather than a flat archive.

## What it does

1. Imports JSON, CSV and TXT conversation exports.
2. Stores protected copies and normalizes chats and messages.
3. Detects deterministic evidence: duplicates, versions, decisions, tasks and explicit state changes.
4. Uses GPT-5.6 to reconstruct projects and operational memory through the OpenAI Responses API.
5. Generates one global proposal with safe operations and clearly separated exceptions.
6. Lets the user approve, correct, reject or leave ambiguous cases unchanged.
7. Shows a mandatory before/after preview.
8. Applies only authorized operations to a derived simulated workspace.
9. Records a complete audit trail.
10. Restores the exact previous state with Undo while preserving audit history.

## Demo results

| Metric | Result |
|---|---:|
| Source files | 3 |
| Conversations | 33 |
| Messages | 51 |
| Deterministic findings | 45 |
| Evidence records | 61 |
| Reconstructed projects | 7 |
| Memberships | 29 |
| Global proposals | 20 |
| Safe proposals | 16 |
| Exceptions | 4 |
| Audit events | 9 |
| Original files modified | 0 |

## Core workflow

```text
Import
→ deterministic evidence
→ GPT-5.6 project reconstruction
→ global proposal
→ review by exception
→ before/after preview
→ simulated apply
→ audit
→ exact Undo
```

## Technology

- **Frontend:** React, TypeScript, Vite
- **Backend:** Python, FastAPI, Pydantic
- **Persistence:** SQLite, SQLAlchemy
- **AI:** OpenAI Responses API, `gpt-5.6`, Structured Outputs with Pydantic
- **Testing:** pytest, Vitest, contract validators and end-to-end API flows

## Quick start

### Requirements

- Python 3.11+
- Node.js 20+
- npm

### Linux / macOS

```bash
cp .env.example .env
./scripts/setup.sh
./scripts/start-dev.sh
```

### Windows PowerShell

```powershell
Copy-Item .env.example .env
.\scripts\setup.ps1
.\scripts\start-dev.ps1
```

Open `http://localhost:5173`.

The included **DEMO · PRECOMPUTED** mode works without an API key. It uses the frozen canonical expected output and is clearly labelled as precomputed.

To enable live semantic reconstruction, set `OPENAI_API_KEY` in `.env`. The key is read only by the backend.

## How to test the complete workflow

1. Open **Import** and import the approved demo dataset.
2. Open **Evidence** and run deterministic analysis.
3. Open **Projects & memory** and run the reproducible semantic reconstruction.
4. Open **Proposals & Undo** and generate the global proposal.
5. Approve the safe batch.
6. Review the four exceptions.
7. Generate the before/after preview.
8. Apply the simulated organization.
9. Inspect the audit history and confirm `Originals modified: 0`.
10. Undo the operation and confirm that the restored hash equals the previous hash.

Automated API walkthrough:

```bash
.venv/bin/python scripts/demo_api_flow.py
```

Full release validation:

```bash
./scripts/release-check.sh
```

Windows:

```powershell
.\scriptselease-check.ps1
```

## GPT-5.6 integration

LIVE mode calls the official OpenAI Responses API through `responses.parse` and validates a strict Pydantic Structured Output contract. GPT-5.6 reconstructs semantic project relationships and operational memory: project identity, current state, versions, decisions, pending tasks, blockers and ambiguous memberships.

GPT-5.6 cannot directly apply changes. Deterministic application code validates IDs, protects originals, calculates canonical state hashes, applies only authorized proposals and performs Undo.

## How Codex was used

Codex accelerated the full engineering workflow:

- translated the product rules into a stable architecture;
- created the React/FastAPI/SQLite monorepo;
- implemented import normalization and immutable storage;
- built deterministic evidence extraction;
- integrated GPT-5.6 Structured Outputs;
- implemented the proposal, review, preview, apply, audit and Undo workflow;
- generated and executed regression tests;
- performed clean-install and release validation;
- prepared technical and submission documentation.

Human decisions remained authoritative for product scope, state definitions, immutable originals, review-by-exception, approval gates, the deterministic/semantic boundary, and reversible application.

See [Codex and GPT-5.6](docs/CODEX_AND_GPT56.md) and [Build history](docs/BUILD_HISTORY.md).

## Architecture and integrity

The system separates:

1. immutable source copies;
2. normalized chats and messages;
3. deterministic findings and evidence;
4. semantic project memory;
5. proposals awaiting authorization;
6. simulated workspace state;
7. audit and Undo snapshots.

Apply and Undo operate only on the simulated workspace. Exact SHA-256 state hashes prevent unsafe restoration over an unrelated state.

## Repository map

```text
backend/       FastAPI routes, services, models and tests
frontend/      React/TypeScript interface and tests
demo-data/     Anonymized source files and canonical expected results
docs/          Architecture, security, testing and submission materials
scripts/       Setup, startup, validation and demo automation
screenshots/   Final product screenshots
tests/         Contracts and acceptance matrices
```

## Privacy and security

- Demo data is anonymized and repository-safe.
- Real exports, runtime databases and secrets are excluded.
- API keys never reach the frontend.
- OpenAI response storage is disabled with `store=false`.
- Original content is not edited, renamed, merged or deleted.

## Limitations

- The prototype does not access or modify a real ChatGPT account.
- File import is local; there is no authentication or multi-user collaboration.
- The reproducible demo uses precomputed semantic output.
- LIVE mode requires the entrant or evaluator to provide an OpenAI API key.
- Organization changes are simulated rather than applied to ChatGPT.

## Build Week track

**Apps for Your Life** — personal productivity for people who need to recover and organize knowledge accumulated across months of AI conversations.

## Independent prototype notice

This is an independent prototype created for OpenAI Build Week. It is not an official OpenAI or ChatGPT feature and does not use private ChatGPT APIs.

## License

MIT. See [LICENSE](LICENSE).
