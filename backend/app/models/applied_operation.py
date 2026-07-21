from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AppliedOperation(Base):
    __tablename__ = "applied_operations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    proposal_run_id: Mapped[str] = mapped_column(
        ForeignKey("proposal_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="APPLIED", index=True)
    before_state_json: Mapped[str] = mapped_column(Text, nullable=False)
    after_state_json: Mapped[str] = mapped_column(Text, nullable=False)
    before_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    after_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    applied_proposal_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    undone_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    originals_modified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    proposal_run = relationship("ProposalRun", back_populates="operations")
    undo_operations = relationship("UndoOperation", back_populates="applied_operation", cascade="all, delete-orphan")
