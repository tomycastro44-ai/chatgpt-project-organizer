# Devpost submission — ready-to-paste content

## Project name

ChatGPT Project Organizer

## Track

Apps for Your Life

## Tagline

Turn months of scattered AI conversations into structured, reviewable and reversible projects.

## Short description

ChatGPT Project Organizer imports exported conversations, reconstructs project context with deterministic evidence and GPT-5.6, recovers current versions and forgotten tasks, and proposes a complete organization plan. Users review only ambiguous cases, preview every change, apply authorized operations to a simulated workspace, and Undo exactly while original conversations remain untouched.

## Inspiration

People use AI conversations as an informal workspace for months. Over time, active projects become mixed with old versions, repeated decisions, forgotten tasks and unrelated questions. Existing chat lists show chronology, but they do not reconstruct the current operational state of a project.

## What it does

The application imports JSON, CSV and TXT exports, preserves protected source copies, normalizes chats and messages, extracts deterministic evidence, and uses GPT-5.6 to reconstruct projects and operational memory. It identifies current and obsolete versions, approved and superseded decisions, pending tasks, project states, duplicates and ambiguous memberships.

Instead of asking the user to organize every chat, it generates one global proposal. Safe operations can be approved as a batch. Only exceptions require individual correction or rejection. A mandatory preview shows the simulated before/after state. Apply changes only a derived workspace, records an audit trail and supports exact Undo. Originals are never modified.

## How we built it

The frontend uses React, TypeScript and Vite. The backend uses FastAPI, Pydantic, SQLAlchemy and SQLite. Deterministic services own import integrity, chronology, duplicate detection, evidence, state hashing, apply and Undo. GPT-5.6 is integrated through the OpenAI Responses API with `responses.parse` and Pydantic Structured Outputs for semantic project reconstruction.

The demo includes a clearly labelled precomputed mode for reliable evaluation without external services. LIVE mode becomes available when an OpenAI API key is configured server-side.

## How Codex was used

Codex served as the primary engineering agent. It accelerated the monorepo foundation, API contracts, React interface, import adapters, deterministic evidence engine, GPT-5.6 integration, reversible workflow, tests, clean-install validation and final documentation. Human decisions controlled product scope, immutable originals, evidence precedence, review-by-exception and approval gates.

## How GPT-5.6 was used

GPT-5.6 reconstructs semantic project identity and operational memory from normalized conversations plus deterministic evidence. It returns projects, states, versions, decisions, tasks, blockers, memberships and exceptions through a strict Structured Output contract. GPT-5.6 cannot directly change the workspace; deterministic code validates output and controls proposals, apply and Undo.

## Challenges

The central challenge was combining semantic interpretation with deterministic safety. A language model can understand context, but project organization must remain reproducible, auditable and reversible. We solved this by separating immutable sources, deterministic evidence, semantic memory, proposals, simulated state and audit snapshots.

## Accomplishments

- Complete end-to-end workflow.
- 33-chat anonymized test dataset with exact expected results.
- 45 deterministic findings and 61 evidence records.
- 7 reconstructed projects and 29 memberships.
- 20 proposals with review by exception.
- Exact Undo verified by matching SHA-256 state hashes.
- 63 backend/contract tests, 4 frontend tests and 50 integrated acceptance cases.
- Clean installation and zero production npm vulnerabilities.

## What we learned

AI organization is most useful when it reduces manual review without removing human authority. The strongest design was not automatic reorganization; it was automatic interpretation combined with explicit approval, evidence and reversibility.

## What is next

Future work includes direct user-authorized connectors, incremental analysis, richer project timelines, collaborative review, calibrated confidence evaluation and optional native integration with conversation platforms.

## Built with

React, TypeScript, Vite, Python, FastAPI, Pydantic, SQLAlchemy, SQLite, pytest, Vitest, OpenAI Responses API, GPT-5.6 and Codex.

## Required final links and identifiers

- Repository URL: `ADD_BEFORE_SUBMISSION`
- Public YouTube demo: `ADD_BEFORE_SUBMISSION`
- Codex `/feedback` Session ID: `ADD_BEFORE_SUBMISSION`
