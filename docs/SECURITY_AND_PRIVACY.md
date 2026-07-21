# Security and privacy

## Data handling

- Imported source files are copied to a dedicated runtime directory.
- Stored copies receive randomized filenames and read-only permissions when supported by the operating system.
- User-provided filenames are sanitized and path traversal is blocked.
- Source contents and normalized conversations are not modified by proposal application or Undo.
- Runtime databases and imported files are excluded from version control.

## OpenAI integration

- `OPENAI_API_KEY` is a backend-only environment variable.
- The frontend never receives the key.
- LIVE semantic analysis uses the Responses API with `store=false`.
- DEMO mode performs no external AI request and is visibly marked as precomputed.

## Input controls

- Supported formats are JSON, CSV and TXT.
- File count and file size limits are configurable.
- Unsupported files and parsing errors are isolated instead of corrupting the batch.
- SQLite foreign keys are enabled.

## Known deployment boundary

The MVP has no authentication and is intended for local evaluation or a controlled demonstration environment. It must not be exposed as a public multi-user service without authentication, authorization, rate limiting and production secret management.
