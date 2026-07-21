from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_semantic_layer_files_and_api_contract_exist():
    required = [
        "backend/app/models/semantic_run.py",
        "backend/app/models/project.py",
        "backend/app/models/project_membership.py",
        "backend/app/models/project_evidence.py",
        "backend/app/models/semantic_exception.py",
        "backend/app/schemas/semantic_contracts.py",
        "backend/app/schemas/semantic.py",
        "backend/app/services/semantic_service.py",
        "backend/app/api/routes/semantic.py",
        "frontend/src/pages/ProjectsPage.tsx",
    ]
    assert all((ROOT / path).is_file() for path in required)


def test_openai_contract_is_server_side_responses_api_and_structured_output():
    service = (ROOT / "backend/app/services/semantic_service.py").read_text(encoding="utf-8")
    assert "client.responses.parse" in service
    assert "text_format=SemanticAnalysisPayload" in service
    assert "store=False" in service
    assert "OPENAI_API_KEY" in (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "openai_api_key" not in (ROOT / "frontend/src/api/client.ts").read_text(encoding="utf-8").lower()


def test_demo_mode_is_explicitly_labelled_and_not_presented_as_live():
    page = (ROOT / "frontend/src/pages/ProjectsPage.tsx").read_text(encoding="utf-8")
    assert "DEMO · PRECOMPUTED" in page
    assert "approved demo" in page.lower()
    assert "never presented as a live model result" in page


def test_project_memory_contract_contains_required_fields():
    schema = (ROOT / "backend/app/schemas/semantic_contracts.py").read_text(encoding="utf-8")
    for field in [
        "current_version", "previous_versions", "discarded_versions", "approved_decisions",
        "superseded_decisions", "pending_tasks", "blockers", "last_confirmed_advance",
        "next_probable_step", "memberships", "evidences",
    ]:
        assert field in schema
