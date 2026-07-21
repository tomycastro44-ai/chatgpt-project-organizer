from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ot009_import_contract_files_exist():
    required = [
        "backend/app/models/import_batch.py",
        "backend/app/models/source_file.py",
        "backend/app/models/chat.py",
        "backend/app/models/message.py",
        "backend/app/models/import_issue.py",
        "backend/app/services/import_parsers.py",
        "backend/app/services/import_storage.py",
        "backend/app/services/import_service.py",
        "backend/app/api/routes/imports.py",
        "frontend/src/pages/ImportPage.tsx",
        "tests/matrices/ot009_acceptance_matrix.csv",
    ]
    assert all((ROOT / relative).exists() for relative in required)


def test_import_layer_remains_separate_from_proposals_apply_and_undo():
    import_routes = (ROOT / "backend/app/api/routes/imports.py").read_text(encoding="utf-8").lower()
    import_service = (ROOT / "backend/app/services/import_service.py").read_text(encoding="utf-8").lower()
    assert "proposalrun" not in import_routes + import_service
    assert "appliedoperation" not in import_routes + import_service
    assert "undooperation" not in import_routes + import_service
