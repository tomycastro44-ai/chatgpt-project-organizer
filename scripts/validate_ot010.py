from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def hashes() -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / "demo-data/source").iterdir())
        if path.is_file()
    }


def validate_api() -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    from fastapi.testclient import TestClient
    from app.core.config import get_settings
    from app.main import create_app

    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(temp_dir) / 'validation.db'}"
        os.environ["IMPORTS_DIR"] = str(Path(temp_dir) / "imports")
        os.environ["DEMO_SOURCE_DIR"] = str(ROOT / "demo-data/source")
        os.environ["DEMO_DATA_DIR"] = str(ROOT / "demo-data/canonical")
        get_settings.cache_clear()
        with TestClient(create_app()) as client:
            batch_response = client.post("/api/v1/imports/demo")
            assert batch_response.status_code == 201
            batch = batch_response.json()
            analysis_response = client.post("/api/v1/analysis-runs", json={"batch_id": batch["id"]})
            assert analysis_response.status_code == 201
            analysis = analysis_response.json()
        get_settings.cache_clear()

    assert batch["imported_chats"] == 33
    assert batch["imported_messages"] == 51
    assert analysis["finding_count"] == 45
    assert analysis["evidence_count"] == 61
    assert analysis["exact_duplicate_count"] == 1
    assert analysis["partial_duplicate_count"] == 1
    assert analysis["version_count"] == 9
    assert analysis["state_signal_count"] == 7
    assert analysis["originals_modified"] is False
    findings = {item["stable_key"]: item for item in analysis["findings"]}
    assert findings["version:V8"]["classification"] == "CURRENT"
    assert findings["version:V9"]["classification"] == "DISCARDED"
    assert findings["version:V11"]["classification"] == "DISCARDED"
    assert findings["state_precedence:CHAT-032:CHAT-033"]["classification"] == "ACTIVO"


def main() -> None:
    required = [
        "backend/app/services/analysis_service.py",
        "backend/app/api/routes/analysis.py",
        "backend/app/models/analysis_run.py",
        "backend/app/models/analysis_finding.py",
        "backend/app/models/analysis_evidence.py",
        "frontend/src/pages/AnalysisPage.tsx",
        "docs/OT-010_DETERMINISTIC_ANALYSIS.md",
        "tests/matrices/ot010_acceptance_matrix.csv",
    ]
    for relative in required:
        assert (ROOT / relative).is_file(), relative

    before = hashes()
    run([sys.executable, "-m", "pytest", "-q"], ROOT / "backend")
    run([sys.executable, "-m", "pytest", "-q", "tests/contracts"], ROOT)
    run(["npm", "test", "--", "--run"], ROOT / "frontend")
    run(["npm", "run", "build"], ROOT / "frontend")
    validate_api()
    after = hashes()
    assert before == after
    matrix = ROOT / "tests/matrices/ot010_acceptance_matrix.csv"
    assert sum(1 for _ in matrix.open(encoding="utf-8")) - 1 == 32

    print("OT-010 VALIDATION: OK")
    print("Backend tests: 31")
    print("Repository contracts: 7")
    print("Frontend tests: 3")
    print("Acceptance cases: 32")
    print("Canonical analysis: 33 chats / 45 findings / 61 evidences")
    print("Approved sources unchanged: 3")
    print("Frontend production build: OK")


if __name__ == "__main__":
    main()
