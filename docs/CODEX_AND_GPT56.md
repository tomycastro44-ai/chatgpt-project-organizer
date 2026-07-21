# Codex and GPT-5.6

## Codex contribution

Codex was used as the primary engineering agent throughout the build. It accelerated architecture, implementation, testing, debugging, release validation and documentation.

### Work accelerated by Codex

- Monorepo and local development environment.
- React/TypeScript interface and responsive workflow.
- FastAPI contracts and SQLAlchemy persistence.
- Import adapters for JSON, CSV and TXT.
- Immutable source storage and SHA-256 integrity evidence.
- Deterministic detection of duplicates, versions, decisions, tasks and state precedence.
- OpenAI Responses API integration and Pydantic Structured Outputs.
- Proposal generation, persisted review, preview, simulated apply, audit and exact Undo.
- pytest and Vitest suites, acceptance matrices and clean-install release validation.
- Final documentation and submission package.

## Human decisions

The human product owner defined and approved:

- the exact product objective and MVP boundary;
- immutable original data;
- mandatory human approval;
- review by exception;
- project lifecycle states;
- chronological evidence precedence;
- the deterministic/semantic split;
- simulated application rather than modification of ChatGPT;
- exact Undo and preserved audit history.

Codex did not autonomously change these decisions.

## GPT-5.6 integration

GPT-5.6 is used in LIVE mode for semantic reconstruction after deterministic evidence extraction.

### Input

- normalized conversation summaries;
- deterministic findings;
- linked evidence;
- allowed project states and confidence labels.

### Output

A strict Pydantic Structured Output containing:

- detected projects;
- project descriptions and states;
- current, previous and discarded versions;
- approved and superseded decisions;
- pending tasks and blockers;
- confirmed and doubtful memberships;
- exceptions requiring human review;
- supporting evidence references.

### Safety boundary

GPT-5.6 does not apply operations. Model output is validated against known IDs and enums before persistence. Deterministic code owns integrity checks, proposal authorization, state hashing, simulated apply and Undo.

### Reproducible demo

The included `DEMO · PRECOMPUTED` mode uses frozen canonical output. The UI labels it explicitly and never presents it as a live GPT-5.6 call.
