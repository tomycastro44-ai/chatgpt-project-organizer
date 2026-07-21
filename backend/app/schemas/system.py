from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str
    environment: str


class SystemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_version: str
    database: str
    demo_mode: bool
    openai_configured: bool
    originals_immutable: bool


class DemoSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    chats: int
    projects: int
    proposals: int
    safe_proposals: int
    exceptions: int
    acceptance_cases: int
    source_files: int
    originals_immutable: bool
