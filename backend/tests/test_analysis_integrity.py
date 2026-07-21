from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.config import REPOSITORY_ROOT


def file_hashes(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.iterdir())
        if path.is_file()
    }


def test_analysis_does_not_modify_approved_demo_sources(client):
    source_dir = REPOSITORY_ROOT / "demo-data" / "source"
    before = file_hashes(source_dir)
    batch = client.post("/api/v1/imports/demo").json()
    response = client.post("/api/v1/analysis-runs", json={"batch_id": batch["id"]})
    assert response.status_code == 201
    assert response.json()["originals_modified"] is False
    assert file_hashes(source_dir) == before


def test_analysis_evidence_contains_traceable_chat_and_quote(client):
    batch = client.post("/api/v1/imports/demo").json()
    run = client.post("/api/v1/analysis-runs", json={"batch_id": batch["id"]}).json()
    for finding in run["findings"]:
        assert finding["evidences"]
        for evidence in finding["evidences"]:
            assert evidence["chat_external_id"].startswith("CHAT-")
            assert evidence["quote"].strip()
            assert 1 <= evidence["precedence"] <= 8
