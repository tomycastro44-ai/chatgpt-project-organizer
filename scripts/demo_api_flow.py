from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import httpx


REVIEW_DECISIONS: dict[str, tuple[str, dict[str, Any]]] = {
    "P-017": ("REJECT", {}),
    "P-018": ("CORRECT", {"project_key": "PRJ-SCANLINK"}),
    "P-019": ("REJECT", {}),
    "P-020": ("APPROVE", {}),
}


def post(client: httpx.Client, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    response = client.post(path, json=payload)
    response.raise_for_status()
    return response.json()


def run(base_url: str) -> dict[str, Any]:
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=60.0) as client:
        health = client.get("/api/v1/health")
        health.raise_for_status()

        batch = post(client, "/api/v1/imports/demo")
        analysis = post(client, "/api/v1/analysis-runs", {"batch_id": batch["id"]})
        semantic = post(
            client,
            "/api/v1/semantic-runs",
            {"analysis_run_id": analysis["id"], "mode": "DEMO"},
        )
        proposal = post(client, "/api/v1/proposal-runs", {"semantic_run_id": semantic["id"]})
        proposal = post(client, f"/api/v1/proposal-runs/{proposal['id']}/approve-safe")

        for item in proposal["items"]:
            decision = REVIEW_DECISIONS.get(item["stable_key"])
            if decision is None:
                continue
            action, correction = decision
            proposal = post(
                client,
                f"/api/v1/proposal-runs/{proposal['id']}/items/{item['id']}/review",
                {"decision": action, "correction": correction},
            )

        preview = post(client, f"/api/v1/proposal-runs/{proposal['id']}/preview")
        applied = post(client, f"/api/v1/proposal-runs/{proposal['id']}/apply")
        undone = post(client, f"/api/v1/applied-operations/{applied['id']}/undo")
        audit_response = client.get(f"/api/v1/proposal-runs/{proposal['id']}/audit")
        audit_response.raise_for_status()
        audit = audit_response.json()

    assert batch["imported_chats"] == 33
    assert batch["imported_messages"] == 51
    assert analysis["finding_count"] == 45
    assert analysis["evidence_count"] == 61
    assert semantic["project_count"] == 7
    assert semantic["exception_count"] == 4
    assert proposal["safe_count"] == 16
    assert proposal["exception_count"] == 4
    assert preview["unresolved_exception_ids"] == []
    assert len(preview["proposed_state"]["projects"]) == 7
    assert applied["after_hash"] == preview["proposed_hash"]
    assert applied["originals_modified"] is False
    assert undone["restored_hash"] == applied["before_hash"]
    assert undone["audit_history_preserved"] is True
    assert undone["originals_modified"] is False
    assert [event["sequence"] for event in audit] == list(range(1, 10))

    return {
        "status": "OK",
        "batch_id": batch["id"],
        "analysis_run_id": analysis["id"],
        "semantic_run_id": semantic["id"],
        "proposal_run_id": proposal["id"],
        "operation_id": applied["id"],
        "chats": batch["imported_chats"],
        "messages": batch["imported_messages"],
        "findings": analysis["finding_count"],
        "evidence": analysis["evidence_count"],
        "projects": semantic["project_count"],
        "proposals": len(proposal["items"]),
        "audit_events": len(audit),
        "apply_hash": applied["after_hash"],
        "restored_hash": undone["restored_hash"],
        "originals_modified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the complete ChatGPT Project Organizer demo through the public API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = run(args.base_url)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
