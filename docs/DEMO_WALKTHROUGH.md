# Demo walkthrough

## Start

```bash
cp .env.example .env
./scripts/setup.sh
./scripts/start-dev.sh
```

Open `http://localhost:5173`.

## Recommended demonstration

1. Open **Import** and load the approved demonstration dataset.
2. Open **Analysis** and run deterministic analysis.
3. Open **Projects** and run semantic reconstruction in **DEMO · PRECOMPUTED** mode.
4. Open **Proposals** and generate the global proposal.
5. Approve the safe batch.
6. Review the four exceptions:
   - reject `CHAT-029` and keep it unclassified;
   - correct `CHAT-014` to `PRJ-SCANLINK`;
   - reject `CHAT-031` and keep it unclassified;
   - approve the partial-duplicate relation for `CHAT-006` without merging.
7. Generate the before/after preview.
8. Apply the simulated organization.
9. Show the audit history and confirm that originals modified equals zero.
10. Undo the operation and show that the restored hash equals the before hash.

## Automated API demonstration

With the backend running:

```bash
.venv/bin/python scripts/demo_api_flow.py
```
