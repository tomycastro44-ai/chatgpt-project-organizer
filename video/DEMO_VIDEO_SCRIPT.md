# Demo video narration and shot list

Target duration: approximately 2 minutes 35 seconds.

## 1. Problem and product — Project memory screen

AI conversations quickly become a second workspace, but after months of use, active projects are mixed with old versions, repeated decisions, forgotten tasks, and unrelated questions. ChatGPT Project Organizer turns exported conversations into structured, evidence-backed, and reversible projects.

## 2. Import — Import screen

The workflow starts by importing JSON, CSV, or TXT. Source files are copied into protected storage, hashed, normalized, and never edited. The included anonymized demo contains thirty-three conversations and fifty-one messages.

## 3. Deterministic evidence — Evidence screen

Before using a language model, deterministic rules identify objective signals: exact and partial duplicates, version precedence, approved or rejected decisions, pending tasks, and explicit project states. Every finding keeps the exact conversation evidence that supports it.

## 4. GPT-5.6 — Projects and memory screen

GPT-5.6 then reconstructs semantic project context through the OpenAI Responses API and a strict Pydantic Structured Output. It identifies seven projects, current and discarded versions, decisions, tasks, blockers, memberships, and ambiguous cases. The reproducible demo is clearly labelled as precomputed; live mode uses GPT-5.6 when an API key is configured.

## 5. Human control — Proposals screen

The application generates one global proposal instead of asking the user to organize every chat. Sixteen safe operations can be approved as a batch. Only four exceptions require correction or rejection, so human attention is focused where it matters.

## 6. Preview, apply, and audit — Preview and applied screens

A mandatory before-and-after preview shows exactly what will change. Applying the proposal updates only a simulated derived workspace. The original conversations remain untouched, and every authorized operation is written to an ordered audit history.

## 7. Undo and build process — Undo screen

Undo restores the exact previous workspace hash while preserving audit history. Codex accelerated the architecture, React and FastAPI implementation, tests, debugging, release validation, and documentation. Human decisions defined immutable originals, evidence precedence, approval gates, and the reversible workflow. The result is a working prototype where AI performs the heavy analysis without removing user control.
