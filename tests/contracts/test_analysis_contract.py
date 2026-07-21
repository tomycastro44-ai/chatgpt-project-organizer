from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_analysis_layer_files_exist():
    required = [
        "backend/app/api/routes/analysis.py",
        "backend/app/models/analysis_run.py",
        "backend/app/models/analysis_finding.py",
        "backend/app/models/analysis_evidence.py",
        "backend/app/services/analysis_service.py",
        "backend/app/schemas/analysis.py",
    ]
    for relative in required:
        assert (ROOT / relative).is_file(), relative


def test_analysis_contract_is_deterministic_and_does_not_call_openai():
    service = (ROOT / "backend/app/services/analysis_service.py").read_text(encoding="utf-8")
    assert 'ENGINE_VERSION = "deterministic-ot010-v1"' in service
    assert "openai" not in service.lower()
    assert "originals_modified = False" in service
    assert '"ALTA", "MEDIA", "BAJA"' in service


def test_api_exposes_analysis_run_and_findings_routes():
    route = (ROOT / "backend/app/api/routes/analysis.py").read_text(encoding="utf-8")
    assert 'router = APIRouter(prefix="/analysis-runs"' in route
    assert '@router.post("",' in route
    assert '@router.get("/{run_id}",' in route
    assert '@router.get("/{run_id}/findings"' in route
