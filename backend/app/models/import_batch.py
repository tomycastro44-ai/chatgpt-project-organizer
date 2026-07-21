from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_kind: Mapped[str] = mapped_column(String(24), nullable=False, default="upload")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROCESSING", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_files: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accepted_files: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_files: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_chats: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_messages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issue_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    source_files = relationship("SourceFile", back_populates="batch", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="batch", cascade="all, delete-orphan")
    issues = relationship("ImportIssue", back_populates="batch", cascade="all, delete-orphan")
