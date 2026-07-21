from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import REPOSITORY_ROOT, get_settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("DEMO_DATA_DIR", str(REPOSITORY_ROOT / "demo-data" / "canonical"))
    monkeypatch.setenv("DEMO_SOURCE_DIR", str(REPOSITORY_ROOT / "demo-data" / "source"))
    monkeypatch.setenv("IMPORTS_DIR", str(tmp_path / "imports"))
    get_settings.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()
