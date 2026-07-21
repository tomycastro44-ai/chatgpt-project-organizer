from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    batch_id: Mapped[str] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    engine_version: Mapped[str] = mapped_column(String(64), nullable=False, default="deterministic-ot010-v1")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PROCESSING", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    chat_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    finding_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exact_duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partial_duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    version_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    decision_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    state_signal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    originals_modified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    findings = relationship("AnalysisFinding", back_populates="run", cascade="all, delete-orphan")
    evidences = relationship("AnalysisEvidence", back_populates="run", cascade="all, delete-orphan")
