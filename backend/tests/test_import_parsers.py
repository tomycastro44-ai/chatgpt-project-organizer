from pathlib import Path

from app.core.config import REPOSITORY_ROOT
from app.services.import_parsers import parse_import_file


def test_approved_json_is_normalized():
    path = REPOSITORY_ROOT / "demo-data" / "source" / "chats_primary.json"
    result = parse_import_file(path.name, path.read_bytes())
    assert len(result.chats) == 13
    assert sum(len(chat.messages) for chat in result.chats) > 14
    assert result.issues == []


def test_approved_csv_is_normalized_and_matches_duplicate_fingerprint():
    csv_path = REPOSITORY_ROOT / "demo-data" / "source" / "chats_secondary.csv"
    json_path = REPOSITORY_ROOT / "demo-data" / "source" / "chats_primary.json"
    csv_result = parse_import_file(csv_path.name, csv_path.read_bytes())
    json_result = parse_import_file(json_path.name, json_path.read_bytes())
    csv_chat = next(chat for chat in csv_result.chats if chat.external_id == "CHAT-004")
    json_chat = next(chat for chat in json_result.chats if chat.external_id == "CHAT-003")
    assert len(csv_result.chats) == 9
    assert csv_chat.content_fingerprint == json_chat.content_fingerprint


def test_approved_txt_is_normalized():
    path = REPOSITORY_ROOT / "demo-data" / "source" / "chats_notes.txt"
    result = parse_import_file(path.name, path.read_bytes())
    assert len(result.chats) == 11
    assert result.issues == []


def test_invalid_record_is_isolated():
    result = parse_import_file(
        "mixed.json",
        b'{"conversations":[{"id":"ok","title":"OK","messages":[{"role":"user","content":"hello"}]},{"id":"bad","messages":[]}]}',
    )
    assert [chat.external_id for chat in result.chats] == ["ok"]
    assert result.issues[0].record_reference == "bad"
