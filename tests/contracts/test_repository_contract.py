import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_required_repository_directories_exist():
    for directory in ["frontend", "backend", "demo-data", "docs", "tests", "screenshots", "scripts"]:
        assert (ROOT / directory).is_dir()


def test_runtime_database_is_excluded_from_release_manifest_and_version_control():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/data/*.db" in gitignore
    assert "/data/*.sqlite*" in gitignore

    manifest_path = ROOT / "MANIFEST.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        release_paths = {item["path"] for item in manifest.get("files", [])}
        assert not any(path.startswith("data/") and Path(path).suffix in {".db", ".sqlite", ".sqlite3"} for path in release_paths)
