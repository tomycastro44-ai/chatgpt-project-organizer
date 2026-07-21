# Repository publishing

The O.T. 014 release package is ready to publish as the repository root.

## Recommended public repository name

`chatgpt-project-organizer`

## GitHub command sequence

```bash
git init
git add .
git commit -m "Release ChatGPT Project Organizer MVP"
git branch -M main
git remote add origin REPLACE_WITH_REPOSITORY_URL
git push -u origin main
```

Before pushing:

1. Confirm `.env` does not exist or contains no secrets.
2. Confirm runtime SQLite files are absent.
3. Confirm `node_modules`, `.venv`, caches and build output are absent.
4. Confirm `LICENSE`, README, demo data and screenshots are present.
5. Run the release check.

A public repository should retain the MIT license. A private repository must be shared with the two judging email addresses listed in `SUBMISSION_REQUIREMENTS_VERIFIED.md`.
