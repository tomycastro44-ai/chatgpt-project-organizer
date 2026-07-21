from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalysisCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(min_length=1, max_length=36)


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    kind: str
    quote: str
    precedence: int
    occurred_at: datetime | None
    chat_external_id: str
    message_external_id: str | None


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    stable_key: str
    finding_type: str
    subject: str
    classification: str | None
    confidence: str
    chat_external_id: str | None
    related_chat_external_id: str | None
    details: dict[str, Any]
    evidences: list[EvidenceResponse]


class AnalysisRunSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    batch_id: str
    engine_version: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    chat_count: int
    finding_count: int
    evidence_count: int
    exact_duplicate_count: int
    partial_duplicate_count: int
    version_count: int
    decision_count: int
    task_count: int
    state_signal_count: int
    originals_modified: bool


class AnalysisRunDetailResponse(AnalysisRunSummaryResponse):
    findings: list[FindingResponse]


class FindingListResponse(BaseModel):
    items: list[FindingResponse]
    limit: int = Field(ge=1, le=500)
    offset: int = Field(ge=0)
    total: int = Field(ge=0)
