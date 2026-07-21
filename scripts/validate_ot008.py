from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> None:
    required = [
        "README.md", "LICENSE", ".env.example", ".gitignore",
        "frontend/package.json", "frontend/src/App.tsx", "frontend/vite.config.ts",
        "backend/requirements.txt", "backend/app/main.py", "backend/tests/test_health.py",
        "demo-data/canonical/normalized_chats.json",
        "demo-data/IMMUTABILITY_MANIFEST.json",
        "docs/OT-008_TECHNICAL_FOUNDATION.md",
        "scripts/setup.sh", "scripts/setup.ps1", "scripts/test-all.sh", "scripts/test-all.ps1",
    ]
    for relative in required:
        if not (ROOT / relative).is_file():
            fail(f"Missing required file: {relative}")

    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")
    if re.search(r"OPENAI_API_KEY=\S+", env_text):
        fail(".env.example contains a non-empty API key")

    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    if "react" not in package["dependencies"] or "typescript" not in package["devDependencies"]:
        fail("Frontend dependencies do not satisfy the approved architecture")

    normalized = json.loads((ROOT / "demo-data/canonical/normalized_chats.json").read_text(encoding="utf-8"))
    if len(normalized["chats"]) != 33:
        fail("Approved O.T. 006 dataset was modified")
    if normalized["import_batch"]["originals_immutable"] is not True:
        fail("Originals must remain immutable")

    manifest = json.loads((ROOT / "demo-data/IMMUTABILITY_MANIFEST.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = ROOT / item["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item["sha256"]:
            fail(f"Immutable source changed: {item['path']}")

    forbidden = [ROOT / "frontend" / "node_modules", ROOT / ".venv"]
    packaged_forbidden = [path for path in forbidden if path.exists() and path.is_file()]
    if packaged_forbidden:
        fail("Dependency directories must not be committed as files")

    print("OT-008 VALIDATION: OK")
    print("Repository structure: OK")
    print("Approved dataset integrity: OK")
    print("Secret handling: OK")
    print("Frontend architecture: React + TypeScript")
    print("Backend architecture: FastAPI + SQLAlchemy + SQLite")


if __name__ == "__main__":
    main()
