from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SemanticRun(Base):
    __tablename__ = "semantic_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    analysis_run_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mode: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PROCESSING", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    input_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    openai_response_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    project_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    membership_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exception_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    independent_chat_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unclassified_chat_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    independent_chat_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    unclassified_chat_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    originals_modified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    analysis_run = relationship("AnalysisRun")
    projects = relationship("Project", back_populates="semantic_run", cascade="all, delete-orphan")
    exceptions = relationship("SemanticException", back_populates="semantic_run", cascade="all, delete-orphan")
