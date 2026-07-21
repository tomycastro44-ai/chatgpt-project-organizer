from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProposalRun(Base):
    __tablename__ = "proposal_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    semantic_run_id: Mapped[str] = mapped_column(
        ForeignKey("semantic_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="READY", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    safe_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exception_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    safe_batch_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    originals_modified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    semantic_run = relationship("SemanticRun")
    items = relationship("ProposalItem", back_populates="proposal_run", cascade="all, delete-orphan")
    reviews = relationship("UserReview", back_populates="proposal_run", cascade="all, delete-orphan")
    operations = relationship("AppliedOperation", back_populates="proposal_run", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="proposal_run", cascade="all, delete-orphan")
