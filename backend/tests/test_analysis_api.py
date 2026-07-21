from __future__ import annotations

from collections import Counter


def import_demo(client):
    response = client.post("/api/v1/imports/demo")
    assert response.status_code == 201
    return response.json()


def run_demo_analysis(client):
    batch = import_demo(client)
    response = client.post("/api/v1/analysis-runs", json={"batch_id": batch["id"]})
    assert response.status_code == 201
    return batch, response.json()


def finding_by_key(run: dict, stable_key: str) -> dict:
    return next(item for item in run["findings"] if item["stable_key"] == stable_key)


def test_analysis_requires_existing_import_batch(client):
    response = client.post("/api/v1/analysis-runs", json={"batch_id": "00000000-0000-0000-0000-000000000000"})
    assert response.status_code == 404


def test_demo_analysis_completes_with_reproducible_counts(client):
    _, run = run_demo_analysis(client)
    assert run["status"] == "COMPLETED"
    assert run["engine_version"] == "deterministic-ot010-v1"
    assert run["chat_count"] == 33
    assert run["finding_count"] == 45
    assert run["evidence_count"] == 61
    assert run["originals_modified"] is False
    assert {
        "exact_duplicate_count": run["exact_duplicate_count"],
        "partial_duplicate_count": run["partial_duplicate_count"],
        "version_count": run["version_count"],
        "decision_count": run["decision_count"],
        "task_count": run["task_count"],
        "state_signal_count": run["state_signal_count"],
    } == {
        "exact_duplicate_count": 1,
        "partial_duplicate_count": 1,
        "version_count": 9,
        "decision_count": 16,
        "task_count": 11,
        "state_signal_count": 7,
    }


def test_exact_duplicate_is_detected_without_deleting_original(client):
    _, run = run_demo_analysis(client)
    finding = finding_by_key(run, "exact_duplicate:CHAT-004:CHAT-003")
    assert finding["classification"] == "EXACT_DUPLICATE"
    assert finding["confidence"] == "ALTA"
    assert finding["chat_external_id"] == "CHAT-004"
    assert finding["related_chat_external_id"] == "CHAT-003"
    assert finding["details"]["similarity"] == 1.0
    assert len(finding["evidences"]) == 2


def test_partial_duplicate_requires_review_and_is_not_merged(client):
    _, run = run_demo_analysis(client)
    finding = finding_by_key(run, "partial_duplicate:CHAT-005:CHAT-006")
    assert finding["classification"] == "REVIEW_REQUIRED"
    assert finding["confidence"] == "MEDIA"
    assert finding["details"]["automatic_merge"] is False
    assert "pdf" in finding["details"]["shared_terms"]


def test_version_precedence_resolves_expected_current_previous_and_discarded(client):
    _, run = run_demo_analysis(client)
    expected = {
        "version:V12": "CURRENT",
        "version:V10": "PREVIOUS",
        "version:V11": "DISCARDED",
        "version:V8": "CURRENT",
        "version:V9": "DISCARDED",
        "version:V9.1": "DISCARDED",
        "version:V2": "CURRENT",
        "version:1.0.9": "CURRENT",
        "version:V41": "CURRENT",
    }
    actual = {item["stable_key"]: item["classification"] for item in run["findings"] if item["finding_type"] == "VERSION_STATUS"}
    assert actual == expected


def test_version_status_uses_clause_context_not_whole_message(client):
    _, run = run_demo_analysis(client)
    v8 = finding_by_key(run, "version:V8")
    v9 = finding_by_key(run, "version:V9")
    assert v8["classification"] == "CURRENT"
    assert v9["classification"] == "DISCARDED"
    assert v8["chat_external_id"] == "CHAT-009"


def test_pronoun_version_decision_is_linked_to_previous_version_reference(client):
    _, run = run_demo_analysis(client)
    v11 = finding_by_key(run, "version:V11")
    quotes = [item["quote"] for item in v11["evidences"]]
    assert "No queda estable. No usar esta versión como base." in quotes
    assert v11["classification"] == "DISCARDED"


def test_decisions_and_tasks_are_persisted_with_allowed_confidence(client):
    _, run = run_demo_analysis(client)
    decisions = [item for item in run["findings"] if item["finding_type"] == "DECISION"]
    tasks = [item for item in run["findings"] if item["finding_type"] == "TASK"]
    assert len(decisions) == 16
    assert len(tasks) == 11
    assert {item["confidence"] for item in decisions + tasks}.issubset({"ALTA", "MEDIA", "BAJA"})
    assert any(item["classification"] == "REPLACED" and item["chat_external_id"] == "CHAT-033" for item in decisions)
    assert any(item["chat_external_id"] == "CHAT-029" and item["confidence"] == "BAJA" for item in tasks)


def test_state_precedence_prefers_latest_explicit_evidence(client):
    _, run = run_demo_analysis(client)
    finding = finding_by_key(run, "state_precedence:CHAT-032:CHAT-033")
    assert finding["classification"] == "ACTIVO"
    assert finding["confidence"] == "ALTA"
    assert finding["details"]["previous_state"] == "CERRADO"
    assert finding["details"]["current_state"] == "ACTIVO"
    assert finding["details"]["rule"] == "latest explicit evidence"


def test_findings_can_be_filtered_by_type_and_confidence(client):
    _, run = run_demo_analysis(client)
    response = client.get(f"/api/v1/analysis-runs/{run['id']}/findings", params={"finding_type": "PARTIAL_DUPLICATE", "confidence": "MEDIA"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["stable_key"] == "partial_duplicate:CHAT-005:CHAT-006"


def test_analysis_history_and_detail_are_available(client):
    batch, run = run_demo_analysis(client)
    listed = client.get("/api/v1/analysis-runs", params={"batch_id": batch["id"]})
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == run["id"]
    detail = client.get(f"/api/v1/analysis-runs/{run['id']}")
    assert detail.status_code == 200
    assert detail.json()["finding_count"] == 45


def test_repeated_runs_keep_independent_audit_records_and_same_stable_findings(client):
    batch = import_demo(client)
    first = client.post("/api/v1/analysis-runs", json={"batch_id": batch["id"]}).json()
    second = client.post("/api/v1/analysis-runs", json={"batch_id": batch["id"]}).json()
    assert first["id"] != second["id"]
    assert {item["stable_key"] for item in first["findings"]} == {item["stable_key"] for item in second["findings"]}
    assert first["finding_count"] == second["finding_count"] == 45


def test_finding_type_distribution_is_stable(client):
    _, run = run_demo_analysis(client)
    distribution = Counter(item["finding_type"] for item in run["findings"])
    assert distribution == {
        "DECISION": 16,
        "TASK": 11,
        "VERSION_STATUS": 9,
        "STATE_SIGNAL": 6,
        "STATE_PRECEDENCE": 1,
        "EXACT_DUPLICATE": 1,
        "PARTIAL_DUPLICATE": 1,
    }
