from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ProposalRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    semantic_run_id: str


class ProposalReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["APPROVE", "CORRECT", "REJECT", "KEEP_UNCHANGED"]
    correction: dict[str, Any] = Field(default_factory=dict)
    note: str | None = None


class UserReviewResponse(BaseModel):
    id: str
    decision: str
    correction: dict[str, Any]
    note: str | None
    created_at: datetime


class ProposalItemResponse(BaseModel):
    id: str
    stable_key: str
    operation: str
    title: str
    reason: str
    confidence: str
    review_required: bool
    status: str
    target_ids: list[str]
    candidate_project_keys: list[str]
    evidence_ids: list[str]
    payload: dict[str, Any]
    latest_review: UserReviewResponse | None


class ProposalRunSummaryResponse(BaseModel):
    id: str
    semantic_run_id: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    safe_count: int
    exception_count: int
    safe_batch_approved: bool
    reviewed_exception_count: int
    unresolved_exception_count: int
    originals_modified: bool


class ProposalRunResponse(ProposalRunSummaryResponse):
    items: list[ProposalItemResponse]


class WorkspaceStateResponse(BaseModel):
    semantic_run_id: str
    projects: list[dict[str, Any]]
    exact_duplicates: list[dict[str, Any]]
    partial_duplicates: list[dict[str, Any]]
    independent_chat_ids: list[str]
    unclassified_chat_ids: list[str]
    protected_chat_ids: list[str]
    originals_modified: bool


class PreviewResponse(BaseModel):
    proposal_run_id: str
    before_state: WorkspaceStateResponse
    proposed_state: WorkspaceStateResponse
    before_hash: str
    proposed_hash: str
    approved_proposal_ids: list[str]
    unresolved_exception_ids: list[str]
    originals_modified: bool


class AppliedOperationResponse(BaseModel):
    id: str
    proposal_run_id: str
    status: str
    before_hash: str
    after_hash: str
    applied_proposal_ids: list[str]
    applied_at: datetime
    undone_at: datetime | None
    state: WorkspaceStateResponse
    originals_modified: bool


class UndoOperationResponse(BaseModel):
    id: str
    applied_operation_id: str
    status: str
    restored_hash: str
    created_at: datetime
    audit_history_preserved: bool
    originals_modified: bool
    state: WorkspaceStateResponse


class AuditEventResponse(BaseModel):
    id: str
    sequence: int
    event_type: str
    payload: dict[str, Any]
    applied_operation_id: str | None
    created_at: datetime
