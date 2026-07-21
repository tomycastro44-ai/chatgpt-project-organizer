from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    required = [
        "backend/app/services/semantic_service.py",
        "backend/app/schemas/semantic_contracts.py",
        "backend/app/api/routes/semantic.py",
        "frontend/src/pages/ProjectsPage.tsx",
        "docs/OT-011_SEMANTIC_PROJECT_MEMORY.md",
        "tests/matrices/ot011_acceptance_matrix.csv",
    ]
    for item in required:
        assert (ROOT / item).is_file(), item

    with (ROOT / "tests/matrices/ot011_acceptance_matrix.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 48
    assert len({row["case_id"] for row in rows}) == 48

    manifest = json.loads((ROOT / "demo-data/IMMUTABILITY_MANIFEST.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = ROOT / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]

    frontend = (ROOT / "frontend/src/api/client.ts").read_text(encoding="utf-8").lower()
    assert "openai_api_key" not in frontend
    service = (ROOT / "backend/app/services/semantic_service.py").read_text(encoding="utf-8")
    assert "client.responses.parse" in service
    assert "store=False" in service

    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(temp_dir) / 'validate.db'}"
        os.environ["IMPORTS_DIR"] = str(Path(temp_dir) / "imports")
        os.environ["DEMO_DATA_DIR"] = str(ROOT / "demo-data/canonical")
        os.environ["DEMO_SOURCE_DIR"] = str(ROOT / "demo-data/source")
        os.environ.pop("OPENAI_API_KEY", None)

        from app.core.config import get_settings
        from app.main import create_app

        get_settings.cache_clear()
        with TestClient(create_app()) as client:
            imported = client.post("/api/v1/imports/demo")
            assert imported.status_code == 201
            assert imported.json()["imported_chats"] == 33
            analysis = client.post("/api/v1/analysis-runs", json={"batch_id": imported.json()["id"]})
            assert analysis.status_code == 201
            semantic = client.post(
                "/api/v1/semantic-runs",
                json={"analysis_run_id": analysis.json()["id"], "mode": "DEMO"},
            )
            assert semantic.status_code == 201
            payload = semantic.json()
            assert payload["project_count"] == 7
            assert payload["exception_count"] == 4
            assert payload["provider"] == "APPROVED_DEMO_FIXTURE"
            assert payload["originals_modified"] is False
            assert "CHAT-004" not in {
                membership["chat_external_id"]
                for project in payload["projects"]
                for membership in project["memberships"]
            }
        get_settings.cache_clear()

    print("OT-011 VALIDATION: OK")
    print("Projects: 7")
    print("Exceptions: 4")
    print("Acceptance cases: 48")
    print("Responses API contract: OK")
    print("Original integrity: OK")


if __name__ == "__main__":
    main()
