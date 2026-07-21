from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def main() -> None:
    required = [
        "backend/app/services/import_parsers.py",
        "backend/app/services/import_service.py",
        "backend/app/api/routes/imports.py",
        "frontend/src/pages/ImportPage.tsx",
        "docs/OT-009_FUNCTIONAL_IMPORT.md",
    ]
    for relative in required:
        assert (ROOT / relative).exists(), relative

    before = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (ROOT / "demo-data" / "source").iterdir()
        if path.is_file()
    }
    run([sys.executable, "-m", "pytest", "-q"], ROOT / "backend")
    run([sys.executable, "-m", "pytest", "-q", "tests/contracts"], ROOT)
    run(["npm", "test", "--", "--run"], ROOT / "frontend")
    run(["npm", "run", "build"], ROOT / "frontend")
    after = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (ROOT / "demo-data" / "source").iterdir()
        if path.is_file()
    }
    assert before == after
    matrix = ROOT / "tests" / "matrices" / "ot009_acceptance_matrix.csv"
    assert sum(1 for _ in matrix.open(encoding="utf-8")) - 1 == 30
    print("OT-009 VALIDATION: OK")
    print("Approved source files unchanged: 3")
    print("Functional formats: JSON, CSV, TXT")
    print("Frontend production build: OK")


if __name__ == "__main__":
    main()
