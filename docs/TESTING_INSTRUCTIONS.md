# Testing instructions for judges

## Fastest path

1. Install Python 3.11+, Node.js 20+ and npm.
2. Copy `.env.example` to `.env`.
3. Run the setup script.
4. Run the development start script.
5. Open `http://localhost:5173`.

Linux/macOS:

```bash
cp .env.example .env
./scripts/setup.sh
./scripts/start-dev.sh
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
.\scripts\setup.ps1
.\scripts\start-dev.ps1
```

## Recommended judging workflow

1. **Import** — click **Import approved demo dataset**.
2. **Evidence** — click **Run deterministic analysis**.
3. **Projects & memory** — keep `DEMO · reproducible` selected and click **Reconstruct projects**.
4. Inspect project state, current version, decisions, tasks and evidence.
5. **Proposals & Undo** — generate proposals if needed.
6. Approve 16 safe proposals.
7. Review the four exceptions:
   - reject `CHAT-029`;
   - correct `CHAT-014` to `PRJ-SCANLINK`;
   - reject `CHAT-031`;
   - record the partial duplicate for `CHAT-006` without merging.
8. Generate the preview.
9. Apply the simulated organization.
10. Inspect the nine audit events and `Originals modified: 0`.
11. Click **Undo operation** and confirm exact restoration.

Expected result:

- 33 chats, 51 messages;
- 45 deterministic findings, 61 evidence records;
- 7 projects and 29 memberships;
- 20 proposals, 16 safe and 4 exceptions;
- exact Undo with audit history preserved;
- zero original files modified.

## Automated validation

```bash
./scripts/release-check.sh
```

or on Windows:

```powershell
.\scriptselease-check.ps1
```

Automated API demo while the backend is running:

```bash
.venv/bin/python scripts/demo_api_flow.py
```

## LIVE GPT-5.6 mode

Set `OPENAI_API_KEY` in `.env`, restart the backend, choose `LIVE · GPT-5.6`, and run semantic reconstruction. The included demo does not require a key.
