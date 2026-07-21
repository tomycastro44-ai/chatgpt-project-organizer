from __future__ import annotations

from app.core.config import get_settings
from app.schemas.semantic_contracts import (
    SemanticAnalysisPayload,
    SemanticEvidencePayload,
    SemanticExceptionPayload,
    SemanticMembershipPayload,
    SemanticProjectPayload,
)
from app.services.semantic_service import ProviderResult, SemanticService


def prepare_analysis(client):
    batch = client.post("/api/v1/imports/demo").json()
    analysis = client.post("/api/v1/analysis-runs", json={"batch_id": batch["id"]}).json()
    return batch, analysis


def run_demo_semantic(client):
    _, analysis = prepare_analysis(client)
    response = client.post(
        "/api/v1/semantic-runs",
        json={"analysis_run_id": analysis["id"], "mode": "DEMO"},
    )
    assert response.status_code == 201, response.text
    return analysis, response.json()


def test_semantic_capabilities_are_explicit(client):
    response = client.get("/api/v1/semantic-runs/capabilities")
    assert response.status_code == 200
    assert response.json() == {
        "demo_available": True,
        "live_available": False,
        "default_model": "gpt-5.6",
        "responses_api": True,
        "structured_outputs": True,
    }


def test_demo_semantic_run_reconstructs_approved_projects(client):
    _, run = run_demo_semantic(client)
    assert run["status"] == "COMPLETED"
    assert run["mode"] == "DEMO"
    assert run["provider"] == "APPROVED_DEMO_FIXTURE"
    assert run["model"] == "gpt-5.6"
    assert run["project_count"] == 7
    assert run["exception_count"] == 4
    assert run["independent_chat_count"] == 4
    assert run["unclassified_chat_count"] == 1
    assert run["originals_modified"] is False
    assert {item["state"] for item in run["projects"]} >= {
        "ACTIVO", "PENDIENTE", "EN_PAUSA", "CERRADO", "ARCHIVADO"
    }


def test_operational_memory_contains_versions_decisions_and_tasks(client):
    _, run = run_demo_semantic(client)
    routeflow = next(item for item in run["projects"] if item["project_key"] == "PRJ-ROUTEFLOW")
    assert routeflow["current_version"] == "v12"
    assert routeflow["previous_versions"] == ["v10"]
    assert routeflow["discarded_versions"] == ["v11"]
    assert len(routeflow["approved_decisions"]) == 2
    assert len(routeflow["pending_tasks"]) == 2
    assert routeflow["next_probable_step"]
    assert routeflow["evidences"]


def test_recent_explicit_decision_keeps_inventory_active(client):
    _, run = run_demo_semantic(client)
    stock = next(item for item in run["projects"] if item["project_key"] == "PRJ-STOCKCORE")
    assert stock["state"] == "ACTIVO"
    assert stock["current_version"] == "V8 + SCAN"
    assert "V9" in stock["discarded_versions"]
    assert "V9.1" in stock["discarded_versions"]


def test_exact_duplicate_copy_is_not_assigned_as_project_membership(client):
    _, run = run_demo_semantic(client)
    assigned = {
        membership["chat_external_id"]
        for project in run["projects"]
        for membership in project["memberships"]
    }
    assert "CHAT-003" in assigned
    assert "CHAT-004" not in assigned


def test_review_exceptions_remain_unapplied(client):
    _, run = run_demo_semantic(client)
    exceptions = {item["chat_external_id"]: item for item in run["exceptions"]}
    assert set(exceptions) == {"CHAT-006", "CHAT-014", "CHAT-029", "CHAT-031"}
    assert exceptions["CHAT-014"]["candidate_project_keys"] == ["PRJ-SCANLINK", "PRJ-STOCKCORE"]
    assert exceptions["CHAT-029"]["confidence"] == "BAJA"
    assert run["unclassified_chat_ids"] == ["CHAT-029"]


def test_semantic_history_and_detail_are_available(client):
    _, run = run_demo_semantic(client)
    listed = client.get("/api/v1/semantic-runs")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == run["id"]
    detail = client.get(f"/api/v1/semantic-runs/{run['id']}")
    assert detail.status_code == 200
    assert detail.json()["project_count"] == 7


def test_live_mode_requires_server_side_api_key(client):
    _, analysis = prepare_analysis(client)
    response = client.post(
        "/api/v1/semantic-runs",
        json={"analysis_run_id": analysis["id"], "mode": "LIVE"},
    )
    assert response.status_code == 409
    assert "OPENAI_API_KEY" in response.json()["detail"]


class FakeProvider:
    def analyze(self, prompt_payload: dict) -> ProviderResult:
        assert prompt_payload["contract"]["originals_immutable"] is True
        return ProviderResult(
            provider="TEST_STRUCTURED_PROVIDER",
            model="gpt-5.6",
            response_id="resp_test_123",
            payload=SemanticAnalysisPayload(
                projects=[
                    SemanticProjectPayload(
                        project_key="PRJ-TEST",
                        name="Test project",
                        description="Structured provider test.",
                        state="ACTIVO",
                        confidence="ALTA",
                        current_version="v1",
                        previous_versions=[],
                        discarded_versions=[],
                        phase="Testing",
                        approved_decisions=["Keep the current base"],
                        superseded_decisions=[],
                        discarded_items=[],
                        pending_tasks=["Continue testing"],
                        blockers=[],
                        last_confirmed_advance="Provider output validated",
                        next_probable_step="Persist the result",
                        memberships=[
                            SemanticMembershipPayload(
                                chat_id="CHAT-001",
                                status="CONFIRMADA",
                                confidence="ALTA",
                                rationale="The chat names the validated project version.",
                            )
                        ],
                        evidences=[
                            SemanticEvidencePayload(
                                chat_id="CHAT-001",
                                message_id="M-001-1",
                                kind="validated_version",
                                quote="La versión v10 funciona.",
                                precedence=3,
                            )
                        ],
                    )
                ],
                exceptions=[
                    SemanticExceptionPayload(
                        chat_id="CHAT-029",
                        kind="INSUFFICIENT_CONTEXT",
                        confidence="BAJA",
                        candidate_project_keys=[],
                        reason="There is not enough context.",
                    )
                ],
                independent_chat_ids=["CHAT-026"],
                unclassified_chat_ids=["CHAT-029"],
            ),
        )


def test_structured_provider_output_is_validated_and_persisted(client):
    _, analysis = prepare_analysis(client)
    service = SemanticService(client.app.state.database_engine, get_settings(), provider=FakeProvider())
    run = service.run(analysis["id"], "LIVE")
    assert run.provider == "TEST_STRUCTURED_PROVIDER"
    assert run.openai_response_id == "resp_test_123"
    assert run.projects[0].project_key == "PRJ-TEST"
    assert run.projects[0].memberships[0].chat_external_id == "CHAT-001"
    assert run.projects[0].evidences[0].message_external_id == "M-001-1"
    assert run.originals_modified is False


def test_repeated_semantic_runs_keep_independent_audit_records(client):
    _, analysis = prepare_analysis(client)
    first = client.post("/api/v1/semantic-runs", json={"analysis_run_id": analysis["id"], "mode": "DEMO"}).json()
    second = client.post("/api/v1/semantic-runs", json={"analysis_run_id": analysis["id"], "mode": "DEMO"}).json()
    assert first["id"] != second["id"]
    assert first["input_digest"] == second["input_digest"]
    assert first["project_count"] == second["project_count"] == 7
