from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Confidence = Literal["ALTA", "MEDIA", "BAJA"]
ProjectState = Literal["ACTIVO", "PENDIENTE", "EN_PAUSA", "CERRADO", "ARCHIVADO", "REVISION"]
MembershipStatus = Literal["CONFIRMADA", "DUDOSA"]


class SemanticMembershipPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chat_id: str = Field(description="External chat identifier, for example CHAT-003")
    status: MembershipStatus
    confidence: Confidence
    rationale: str


class SemanticEvidencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chat_id: str
    message_id: str | None
    kind: str
    quote: str
    precedence: int = Field(ge=1, le=8)


class SemanticProjectPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_key: str
    name: str
    description: str
    state: ProjectState
    confidence: Confidence
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
    memberships: list[SemanticMembershipPayload]
    evidences: list[SemanticEvidencePayload]


class SemanticExceptionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chat_id: str | None
    kind: str
    confidence: Confidence
    candidate_project_keys: list[str]
    reason: str


class SemanticAnalysisPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    projects: list[SemanticProjectPayload]
    exceptions: list[SemanticExceptionPayload]
    independent_chat_ids: list[str]
    unclassified_chat_ids: list[str]
