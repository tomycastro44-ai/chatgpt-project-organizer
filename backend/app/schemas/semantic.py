from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class SemanticRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_run_id: str
    mode: Literal["DEMO", "LIVE"] = "DEMO"


class SemanticCapabilityResponse(BaseModel):
    demo_available: bool
    live_available: bool
    default_model: str
    responses_api: bool
    structured_outputs: bool


class ProjectMembershipResponse(BaseModel):
    id: str
    chat_external_id: str
    chat_title: str
    status: str
    confidence: str
    rationale: str


class ProjectEvidenceResponse(BaseModel):
    id: str
    chat_external_id: str
    message_external_id: str | None
    kind: str
    quote: str
    precedence: int


class ProjectResponse(BaseModel):
    id: str
    project_key: str
    name: str
    description: str
    state: str
    confidence: str
    current_version: str | None
    previous_versions: list[str]
    discarded_versions: list[str]
    phase: str | None
    approved_decisions: list[str]
    superseded_decisions: list[str]
    discarded_items: list[str]
    pending_tasks: list[str]
    blockers: list[str]
    last_confirmed_advance: str | None
    next_probable_step: str | None
    memberships: list[ProjectMembershipResponse]
    evidences: list[ProjectEvidenceResponse]


class SemanticExceptionResponse(BaseModel):
    id: str
    chat_external_id: str | None
    chat_title: str | None
    kind: str
    confidence: str
    candidate_project_keys: list[str]
    reason: str


class SemanticRunSummaryResponse(BaseModel):
    id: str
    analysis_run_id: str
    mode: str
    model: str
    provider: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    input_digest: str
    openai_response_id: str | None
    project_count: int
    membership_count: int
    exception_count: int
    independent_chat_count: int
    unclassified_chat_count: int
    originals_modified: bool


class SemanticRunResponse(SemanticRunSummaryResponse):
    projects: list[ProjectResponse]
    exceptions: list[SemanticExceptionResponse]
    independent_chat_ids: list[str]
    unclassified_chat_ids: list[str]
