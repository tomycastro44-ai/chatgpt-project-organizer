from pathlib import Path

from app.core.config import REPOSITORY_ROOT, get_settings


def test_demo_import_persists_all_approved_sources(client):
    response = client.post("/api/v1/imports/demo")
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "COMPLETED"
    assert payload["total_files"] == 3
    assert payload["accepted_files"] == 3
    assert payload["rejected_files"] == 0
    assert payload["imported_chats"] == 33
    assert payload["issue_count"] == 0
    assert payload["originals_immutable"] is True

    chats = client.get(f"/api/v1/imports/{payload['id']}/chats?limit=100")
    assert chats.status_code == 200
    items = chats.json()["items"]
    assert len(items) == 33
    assert {item["external_id"] for item in items} >= {"CHAT-001", "CHAT-033"}


def test_uploaded_invalid_file_is_rejected_without_losing_valid_file(client):
    files = [
        ("files", ("valid.json", b'{"conversations":[{"id":"one","title":"One","messages":[{"role":"user","content":"Hello"}]}]}', "application/json")),
        ("files", ("invalid.json", b'{not-json', "application/json")),
    ]
    response = client.post("/api/v1/imports", files=files)
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "COMPLETED_WITH_ERRORS"
    assert payload["accepted_files"] == 1
    assert payload["rejected_files"] == 1
    assert payload["imported_chats"] == 1
    assert any(issue["code"] == "INVALID_JSON" for issue in payload["issues"])


def test_original_demo_files_are_not_modified(client):
    source_dir = REPOSITORY_ROOT / "demo-data" / "source"
    before = {path.name: path.read_bytes() for path in source_dir.iterdir() if path.is_file()}
    response = client.post("/api/v1/imports/demo")
    assert response.status_code == 201
    after = {path.name: path.read_bytes() for path in source_dir.iterdir() if path.is_file()}
    assert before == after

    settings = get_settings()
    stored = list((settings.imports_dir / response.json()["id"] / "originals").iterdir())
    assert len(stored) == 3
    assert all(path.stat().st_size > 0 for path in stored)


def test_import_history_and_detail(client):
    created = client.post("/api/v1/imports/demo").json()
    history = client.get("/api/v1/imports")
    assert history.status_code == 200
    assert history.json()[0]["id"] == created["id"]
    detail = client.get(f"/api/v1/imports/{created['id']}")
    assert detail.status_code == 200
    assert len(detail.json()["source_files"]) == 3


def test_repeated_imports_use_independent_internal_ids(client):
    first = client.post("/api/v1/imports/demo").json()
    second = client.post("/api/v1/imports/demo").json()
    assert first["id"] != second["id"]
    first_chats = client.get(f"/api/v1/imports/{first['id']}/chats?limit=100").json()["items"]
    second_chats = client.get(f"/api/v1/imports/{second['id']}/chats?limit=100").json()["items"]
    assert {chat["external_id"] for chat in first_chats} == {chat["external_id"] for chat in second_chats}
    assert {chat["id"] for chat in first_chats}.isdisjoint({chat["id"] for chat in second_chats})


def test_unsupported_file_is_preserved_and_rejected(client):
    response = client.post(
        "/api/v1/imports",
        files=[("files", ("notes.md", b"not supported", "text/markdown"))],
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["rejected_files"] == 1
    assert payload["imported_chats"] == 0
    assert payload["issues"][0]["code"] == "UNSUPPORTED_FORMAT"


def test_stored_originals_are_read_only_on_supported_platforms(client):
    response = client.post("/api/v1/imports/demo")
    batch_id = response.json()["id"]
    settings = get_settings()
    stored = list((settings.imports_dir / batch_id / "originals").iterdir())
    assert stored
    assert all((path.stat().st_mode & 0o222) == 0 for path in stored)
