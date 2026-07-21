from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImportIssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    source_file_id: str | None
    scope: str
    code: str
    severity: str
    message: str
    record_reference: str | None


class SourceFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    original_name: str
    format: str
    mime_type: str
    size_bytes: int
    sha256: str
    status: str
    chat_count: int
    message_count: int
    error_count: int


class ImportBatchSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    source_kind: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    total_files: int
    accepted_files: int
    rejected_files: int
    imported_chats: int
    imported_messages: int
    issue_count: int


class ImportBatchDetailResponse(ImportBatchSummaryResponse):
    source_files: list[SourceFileResponse]
    issues: list[ImportIssueResponse]
    originals_immutable: bool = True


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    external_id: str | None
    position: int
    role: str
    timestamp: datetime | None
    content: str


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    source_file_id: str
    external_id: str
    title: str
    created_at: datetime | None
    updated_at: datetime | None
    content_fingerprint: str
    source_index: int
    messages: list[MessageResponse]


class ChatListResponse(BaseModel):
    items: list[ChatResponse]
    limit: int = Field(ge=1, le=500)
    offset: int = Field(ge=0)
