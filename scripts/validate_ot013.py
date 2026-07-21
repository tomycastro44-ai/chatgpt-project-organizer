from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

REQUIRED_ENDPOINTS = {
    "/api/v1/health",
    "/api/v1/imports/demo",
    "/api/v1/analysis-runs",
    "/api/v1/semantic-runs/capabilities",
    "/api/v1/semantic-runs",
    "/api/v1/proposal-runs",
    "/api/v1/proposal-runs/{run_id}/approve-safe",
    "/api/v1/proposal-runs/{run_id}/items/{item_id}/review",
    "/api/v1/proposal-runs/{run_id}/preview",
    "/api/v1/proposal-runs/{run_id}/apply",
    "/api/v1/proposal-runs/{run_id}/audit",
    "/api/v1/applied-operations/{operation_id}/undo",
}

REQUIRED_FILES = [
    "README.md",
    "VERSION",
    "CHANGELOG.md",
    "docs/ARCHITECTURE.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/TESTING.md",
    "docs/DEMO_WALKTHROUGH.md",
    "docs/LIMITATIONS.md",
    "scripts/demo_api_flow.py",
    "scripts/release-check.sh",
    "scripts/validate_ot013.py",
    "tests/matrices/ot013_acceptance_matrix.csv",
]

SKIP_PARTS = {".venv", "node_modules", "dist", "__pycache__", ".pytest_cache", ".git"}
TEXT_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".json", ".md", ".txt", ".yml", ".yaml", ".toml", ".ini", ".sh", ".ps1", ".env", ".example"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"OPENAI_API_KEY\s*=\s*[^\s#]+"),
    re.compile(r"api_key\s*=\s*['\"][^'\"]{12,}['\"]"),
]

REVIEW_DECISIONS: dict[str, tuple[str, dict[str, Any]]] = {
    "P-017": ("REJECT", {}),
    "P-018": ("CORRECT", {"project_key": "PRJ-SCANLINK"}),
    "P-019": ("REJECT", {}),
    "P-020": ("APPROVE", {}),
}


def source_hashes() -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / "demo-data" / "source").glob("*"))
        if path.is_file()
    }


def scan_for_secrets() -> None:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.name == ".env.example":
            content = path.read_text(encoding="utf-8", errors="ignore")
            if "OPENAI_API_KEY=" not in content or re.search(r"OPENAI_API_KEY=\S+", content):
                findings.append(".env.example must contain an empty OPENAI_API_KEY")
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"Makefile", "VERSION"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            stripped = line.strip()
            if "re.compile" in stripped or "SECRET_PATTERNS" in stripped or "re.search" in stripped:
                continue
            if SECRET_PATTERNS[0].search(stripped):
                findings.append(str(path.relative_to(ROOT)))
                break
            if path.suffix.lower() in {".env", ".ini", ".toml", ".yaml", ".yml"} and SECRET_PATTERNS[1].search(stripped):
                findings.append(str(path.relative_to(ROOT)))
                break
            if SECRET_PATTERNS[2].search(stripped):
                findings.append(str(path.relative_to(ROOT)))
                break
    assert not findings, f"Potential secret material found: {findings}"


def normalized_workspace(state: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(state))
    result.pop("semantic_run_id", None)
    return result


def complete_flow(client: Any) -> dict[str, Any]:
    batch_response = client.post("/api/v1/imports/demo")
    assert batch_response.status_code == 201, batch_response.text
    batch = batch_response.json()

    analysis_response = client.post("/api/v1/analysis-runs", json={"batch_id": batch["id"]})
    assert analysis_response.status_code == 201, analysis_response.text
    analysis = analysis_response.json()

    semantic_response = client.post(
        "/api/v1/semantic-runs",
        json={"analysis_run_id": analysis["id"], "mode": "DEMO"},
    )
    assert semantic_response.status_code == 201, semantic_response.text
    semantic = semantic_response.json()

    proposal_response = client.post("/api/v1/proposal-runs", json={"semantic_run_id": semantic["id"]})
    assert proposal_response.status_code == 201, proposal_response.text
    proposal = proposal_response.json()

    early_apply = client.post(f"/api/v1/proposal-runs/{proposal['id']}/apply")
    assert early_apply.status_code == 409

    proposal = client.post(f"/api/v1/proposal-runs/{proposal['id']}/approve-safe").json()
    for item in proposal["items"]:
        decision = REVIEW_DECISIONS.get(item["stable_key"])
        if decision is None:
            continue
        action, correction = decision
        review_response = client.post(
            f"/api/v1/proposal-runs/{proposal['id']}/items/{item['id']}/review",
            json={"decision": action, "correction": correction},
        )
        assert review_response.status_code == 200, review_response.text
        proposal = review_response.json()

    preview = client.post(f"/api/v1/proposal-runs/{proposal['id']}/preview").json()
    applied = client.post(f"/api/v1/proposal-runs/{proposal['id']}/apply").json()
    undo_response = client.post(f"/api/v1/applied-operations/{applied['id']}/undo")
    assert undo_response.status_code == 201, undo_response.text
    undone = undo_response.json()
    repeated_undo = client.post(f"/api/v1/applied-operations/{applied['id']}/undo")
    assert repeated_undo.status_code == 409
    audit = client.get(f"/api/v1/proposal-runs/{proposal['id']}/audit").json()

    assert batch["accepted_files"] == 3
    assert batch["imported_chats"] == 33
    assert batch["imported_messages"] == 51
    assert batch["originals_immutable"] is True
    assert analysis["finding_count"] == 45
    assert analysis["evidence_count"] == 61
    assert analysis["exact_duplicate_count"] == 1
    assert analysis["partial_duplicate_count"] == 1
    assert analysis["version_count"] == 9
    assert semantic["mode"] == "DEMO"
    assert semantic["project_count"] == 7
    assert semantic["membership_count"] == 29
    assert semantic["exception_count"] == 4
    assert semantic["independent_chat_count"] == 4
    assert semantic["unclassified_chat_count"] == 1
    assert proposal["safe_count"] == 16
    assert proposal["exception_count"] == 4
    assert proposal["unresolved_exception_count"] == 0
    assert len(proposal["items"]) == 20
    assert preview["unresolved_exception_ids"] == []
    assert len(preview["proposed_state"]["projects"]) == 7
    assert set(preview["proposed_state"]["unclassified_chat_ids"]) == {"CHAT-029", "CHAT-031"}
    assert applied["status"] == "APPLIED"
    assert applied["after_hash"] == preview["proposed_hash"]
    assert applied["originals_modified"] is False
    assert undone["status"] == "COMPLETED"
    assert undone["restored_hash"] == applied["before_hash"]
    assert undone["audit_history_preserved"] is True
    assert undone["originals_modified"] is False
    assert len(audit) == 9
    assert [event["sequence"] for event in audit] == list(range(1, 10))

    return {
        "workspace": normalized_workspace(preview["proposed_state"]),
        "counts": {
            "chats": batch["imported_chats"],
            "messages": batch["imported_messages"],
            "findings": analysis["finding_count"],
            "evidence": analysis["evidence_count"],
            "projects": semantic["project_count"],
            "proposals": len(proposal["items"]),
            "audit": len(audit),
        },
    }


def main() -> None:
    for relative in REQUIRED_FILES:
        assert (ROOT / relative).is_file(), relative

    with (ROOT / "tests" / "matrices" / "ot013_acceptance_matrix.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 50
    assert len({row["case_id"] for row in rows}) == 50

    scan_for_secrets()
    assert "OPENAI_API_KEY" not in "".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (ROOT / "frontend" / "src").rglob("*")
        if path.is_file()
    )

    initial_hashes = source_hashes()
    manifest = json.loads((ROOT / "demo-data" / "IMMUTABILITY_MANIFEST.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = ROOT / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        os.environ["DATABASE_URL"] = f"sqlite:///{temp / 'release.db'}"
        os.environ["IMPORTS_DIR"] = str(temp / "imports")
        os.environ["DEMO_DATA_DIR"] = str(ROOT / "demo-data" / "canonical")
        os.environ["DEMO_SOURCE_DIR"] = str(ROOT / "demo-data" / "source")
        os.environ.pop("OPENAI_API_KEY", None)

        from app.core.config import get_settings
        get_settings.cache_clear()
        from app.main import create_app
        from fastapi.testclient import TestClient

        with TestClient(create_app()) as client:
            health = client.get("/api/v1/health")
            assert health.status_code == 200 and health.json()["status"] == "ok"
            capabilities = client.get("/api/v1/semantic-runs/capabilities").json()
            assert capabilities["demo_available"] is True
            assert capabilities["live_available"] is False
            live_without_key = client.post(
                "/api/v1/semantic-runs",
                json={"analysis_run_id": "missing", "mode": "LIVE"},
            )
            assert live_without_key.status_code in {404, 409}

            openapi = client.get("/openapi.json").json()
            assert REQUIRED_ENDPOINTS.issubset(set(openapi["paths"]))

            first = complete_flow(client)
            second = complete_flow(client)
            assert first["counts"] == second["counts"]
            assert first["workspace"] == second["workspace"]

        get_settings.cache_clear()

    assert source_hashes() == initial_hashes
    from app.services.import_storage import ImportStorage
    assert ImportStorage.sanitize_filename("../../secret.json") == "secret.json"

    print("OT-013 VALIDATION: OK")
    print("Backend and contract tests: delegated to release-check")
    print("Frontend tests and production build: delegated to release-check")
    print("Acceptance cases: 50")
    print("Complete demo executions: 2")
    print("Canonical chats: 33")
    print("Canonical projects: 7")
    print("Canonical proposals: 20")
    print("Audit events per execution: 9")
    print("Exact Undo: OK")
    print("Original integrity: OK")
    print("Secret scan: OK")


if __name__ == "__main__":
    main()
