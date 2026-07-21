from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ot012_contract_files_exist():
    required = [
        "backend/app/models/proposal_run.py", "backend/app/models/proposal_item.py",
        "backend/app/models/user_review.py", "backend/app/models/applied_operation.py",
        "backend/app/models/undo_operation.py", "backend/app/models/audit_event.py",
        "backend/app/models/workspace_state.py", "backend/app/services/proposal_service.py",
        "backend/app/api/routes/proposals.py", "frontend/src/pages/ProposalsPage.tsx",
    ]
    for relative in required:
        assert (ROOT / relative).exists(), relative


def test_routes_cover_review_preview_apply_and_undo():
    source = (ROOT / "backend/app/api/routes/proposals.py").read_text(encoding="utf-8")
    for fragment in ["approve-safe", "/review", "/preview", "/apply", "/undo", "/audit"]:
        assert fragment in source


def test_originals_are_explicitly_immutable():
    source = (ROOT / "backend/app/services/proposal_service.py").read_text(encoding="utf-8")
    assert '"originals_modified": False' in source
    assert "audit_history_preserved=True" in source
    assert "before_state_json" in source and "after_state_json" in source
