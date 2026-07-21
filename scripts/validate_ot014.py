from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "VERSION",
    "CHANGELOG.md",
    "docs/CODEX_AND_GPT56.md",
    "docs/BUILD_HISTORY.md",
    "docs/TESTING_INSTRUCTIONS.md",
    "docs/DEVPOST_SUBMISSION.md",
    "docs/SUBMISSION_REQUIREMENTS_VERIFIED.md",
    "docs/REPOSITORY_PUBLISHING.md",
    "docs/FEEDBACK_SESSION_ID.md",
    "docs/FINAL_SUBMISSION_CHECKLIST.md",
    "docs/OT-014_FINAL_DOCUMENTATION.md",
    "docs/OT-014_REGISTRO_EN_REVISION.json",
    "docs/SUBMISSION_STATUS.json",
    "video/DEMO_VIDEO_SCRIPT.md",
    "video/YOUTUBE_METADATA.md",
    "video/chatgpt_project_organizer_demo_draft.mp4",
    "video/chatgpt_project_organizer_demo_draft.srt",
    "screenshots/final/RELEASE_SCREENSHOTS_OVERVIEW.png",
    "tests/matrices/ot014_acceptance_matrix.csv",
]

DESKTOP_SHOTS = [
    "01_import_release.png",
    "02_analysis_evidence.png",
    "03_project_memory.png",
    "04_proposals_reviewed.png",
    "05_preview_before_after.png",
    "06_applied_audit.png",
    "07_undo_restored.png",
]
MOBILE_SHOTS = ["08_mobile_project_memory.png", "09_mobile_proposals.png"]
FORBIDDEN_PARTS = {".venv", "node_modules", "dist", "__pycache__", ".pytest_cache", ".git"}
FORBIDDEN_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".pyc", ".pyo"}


def media_probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration:stream=codec_type", "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def main() -> None:
    for relative in REQUIRED_FILES:
        assert (ROOT / relative).is_file(), relative

    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "OT014-v1"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for phrase in [
        "How Codex was used",
        "GPT-5.6 integration",
        "How to test the complete workflow",
        "Apps for Your Life",
        "Original files and conversations are never modified",
    ]:
        assert phrase in readme, phrase

    for name in DESKTOP_SHOTS + MOBILE_SHOTS:
        path = ROOT / "screenshots" / "final" / name
        assert path.is_file() and path.stat().st_size > 20_000, name

    video = ROOT / "video" / "chatgpt_project_organizer_demo_draft.mp4"
    probe = media_probe(video)
    duration = float(probe["format"]["duration"])
    stream_types = {stream["codec_type"] for stream in probe["streams"]}
    assert 1 < duration < 180, duration
    assert {"video", "audio"}.issubset(stream_types), stream_types

    srt = (ROOT / "video" / "chatgpt_project_organizer_demo_draft.srt").read_text(encoding="utf-8")
    assert "GPT-5.6" in srt and "Codex" in srt and "00:00:00,000" in srt

    with (ROOT / "tests" / "matrices" / "ot014_acceptance_matrix.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 40
    assert len({row["case_id"] for row in rows}) == 40

    manifest_path = ROOT / "MANIFEST.json"
    assert manifest_path.is_file(), "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in manifest["files"]:
        relative = Path(item["path"])
        assert not any(part in FORBIDDEN_PARTS for part in relative.parts), item["path"]
        assert relative.suffix.lower() not in FORBIDDEN_SUFFIXES, item["path"]
        assert not relative.name.endswith(".tsbuildinfo"), item["path"]

    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=" in env_example
    assert not any(line.startswith("OPENAI_API_KEY=") and line.strip() != "OPENAI_API_KEY=" for line in env_example.splitlines())

    submission = (ROOT / "docs" / "DEVPOST_SUBMISSION.md").read_text(encoding="utf-8")
    assert "ADD_BEFORE_SUBMISSION" in submission
    checklist = (ROOT / "docs" / "FINAL_SUBMISSION_CHECKLIST.md").read_text(encoding="utf-8")
    assert "Repository published" in checklist and "Upload publicly to YouTube" in checklist

    print("OT-014 VALIDATION: OK")
    print("Documentation requirements: OK")
    print(f"Desktop screenshots: {len(DESKTOP_SHOTS)}")
    print(f"Mobile screenshots: {len(MOBILE_SHOTS)}")
    print(f"Video duration: {duration:.2f} seconds")
    print("Video audio stream: OK")
    print("Acceptance cases: 40")
    print("Repository cleanliness: OK")
    print("Account-dependent steps: explicitly isolated")


if __name__ == "__main__":
    main()
