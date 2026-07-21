from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "ChatGPT Project Organizer"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = f"sqlite:///{REPOSITORY_ROOT / 'data' / 'project_organizer.db'}"
    demo_data_dir: Path = REPOSITORY_ROOT / "demo-data" / "canonical"
    demo_source_dir: Path = REPOSITORY_ROOT / "demo-data" / "source"
    imports_dir: Path = REPOSITORY_ROOT / "data" / "imports"
    max_import_file_bytes: int = 10 * 1024 * 1024
    max_import_files: int = 20
    cors_origins: str = "http://localhost:5173"
    openai_api_key: str = Field(default="", repr=False)
    openai_model: str = "gpt-5.6"
    openai_reasoning_effort: str = "medium"
    openai_max_output_tokens: int = 24000

    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def ensure_runtime_directories(self) -> None:
        if self.database_url.startswith("sqlite:///") and ":memory:" not in self.database_url:
            database_path = Path(self.database_url.removeprefix("sqlite:///"))
            if not database_path.is_absolute():
                database_path = REPOSITORY_ROOT / database_path
            database_path.parent.mkdir(parents=True, exist_ok=True)
        self.imports_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_runtime_directories()
    return settings
