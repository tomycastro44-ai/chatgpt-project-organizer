from __future__ import annotations


def build_semantic(client):
    batch = client.post("/api/v1/imports/demo").json()
    analysis = client.post("/api/v1/analysis-runs", json={"batch_id": batch["id"]}).json()
    semantic = client.post("/api/v1/semantic-runs", json={"analysis_run_id": analysis["id"], "mode": "DEMO"}).json()
    return batch, analysis, semantic


def build_proposals(client):
    _, _, semantic = build_semantic(client)
    response = client.post("/api/v1/proposal-runs", json={"semantic_run_id": semantic["id"]})
    assert response.status_code == 201
    return semantic, response.json()


def test_generates_canonical_proposals(client):
    _, run = build_proposals(client)
    assert run["safe_count"] == 16
    assert run["exception_count"] == 4
    assert len(run["items"]) == 20
    assert run["safe_batch_approved"] is False
    assert run["originals_modified"] is False


def test_safe_batch_requires_explicit_approval(client):
    _, run = build_proposals(client)
    blocked = client.post(f"/api/v1/proposal-runs/{run['id']}/apply")
    assert blocked.status_code == 409
    approved = client.post(f"/api/v1/proposal-runs/{run['id']}/approve-safe").json()
    assert approved["safe_batch_approved"] is True
    assert all(item["status"] == "APPROVED" for item in approved["items"] if not item["review_required"])


def test_reviews_exception_with_correction(client):
    _, run = build_proposals(client)
    item = next(item for item in run["items"] if item["stable_key"] == "P-018")
    reviewed = client.post(
        f"/api/v1/proposal-runs/{run['id']}/items/{item['id']}/review",
        json={"decision": "CORRECT", "correction": {"project_key": "PRJ-SCANLINK"}},
    ).json()
    updated = next(value for value in reviewed["items"] if value["id"] == item["id"])
    assert updated["status"] == "CORRECTED"
    assert updated["latest_review"]["correction"]["project_key"] == "PRJ-SCANLINK"


def test_rejects_invalid_project_correction(client):
    _, run = build_proposals(client)
    item = next(item for item in run["items"] if item["stable_key"] == "P-018")
    response = client.post(
        f"/api/v1/proposal-runs/{run['id']}/items/{item['id']}/review",
        json={"decision": "CORRECT", "correction": {"project_key": "UNKNOWN"}},
    )
    assert response.status_code == 422


def test_preview_keeps_unresolved_exceptions_protected(client):
    _, run = build_proposals(client)
    client.post(f"/api/v1/proposal-runs/{run['id']}/approve-safe")
    preview = client.post(f"/api/v1/proposal-runs/{run['id']}/preview").json()
    assert preview["proposed_state"]["originals_modified"] is False
    assert set(preview["proposed_state"]["protected_chat_ids"]) == {"CHAT-006", "CHAT-014", "CHAT-029", "CHAT-031"}
    assert len(preview["proposed_state"]["projects"]) == 7
    assert preview["proposed_state"]["exact_duplicates"][0]["duplicate_chat_id"] == "CHAT-004"


def test_full_review_apply_and_undo(client):
    _, run = build_proposals(client)
    run = client.post(f"/api/v1/proposal-runs/{run['id']}/approve-safe").json()
    decisions = {
        "P-017": {"decision": "REJECT", "correction": {}},
        "P-018": {"decision": "CORRECT", "correction": {"project_key": "PRJ-SCANLINK"}},
        "P-019": {"decision": "REJECT", "correction": {}},
        "P-020": {"decision": "APPROVE", "correction": {}},
    }
    for item in run["items"]:
        if item["stable_key"] in decisions:
            run = client.post(
                f"/api/v1/proposal-runs/{run['id']}/items/{item['id']}/review",
                json=decisions[item["stable_key"]],
            ).json()
    preview = client.post(f"/api/v1/proposal-runs/{run['id']}/preview").json()
    assert preview["unresolved_exception_ids"] == []
    scanlink = next(project for project in preview["proposed_state"]["projects"] if project["project_key"] == "PRJ-SCANLINK")
    assert "CHAT-014" in scanlink["memberships"]
    assert set(preview["proposed_state"]["unclassified_chat_ids"]) == {"CHAT-029", "CHAT-031"}
    assert preview["proposed_state"]["partial_duplicates"][0]["merged"] is False

    applied = client.post(f"/api/v1/proposal-runs/{run['id']}/apply")
    assert applied.status_code == 201
    operation = applied.json()
    assert operation["after_hash"] == preview["proposed_hash"]
    assert operation["originals_modified"] is False

    undone = client.post(f"/api/v1/applied-operations/{operation['id']}/undo")
    assert undone.status_code == 201
    restored = undone.json()
    assert restored["restored_hash"] == operation["before_hash"]
    assert restored["audit_history_preserved"] is True
    assert restored["state"]["projects"] == []
    assert len(restored["state"]["unclassified_chat_ids"]) == 33


def test_audit_is_preserved_after_undo(client):
    _, run = build_proposals(client)
    client.post(f"/api/v1/proposal-runs/{run['id']}/approve-safe")
    operation = client.post(f"/api/v1/proposal-runs/{run['id']}/apply").json()
    client.post(f"/api/v1/applied-operations/{operation['id']}/undo")
    events = client.get(f"/api/v1/proposal-runs/{run['id']}/audit").json()
    assert [event["event_type"] for event in events] == [
        "PROPOSAL_RUN_CREATED", "SAFE_BATCH_APPROVED", "OPERATIONS_APPLIED", "UNDO_EXECUTED"
    ]
    assert [event["sequence"] for event in events] == [1, 2, 3, 4]


def test_second_active_apply_is_blocked(client):
    _, run = build_proposals(client)
    client.post(f"/api/v1/proposal-runs/{run['id']}/approve-safe")
    assert client.post(f"/api/v1/proposal-runs/{run['id']}/apply").status_code == 201
    assert client.post(f"/api/v1/proposal-runs/{run['id']}/apply").status_code == 409
