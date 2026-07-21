from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProposalItem(Base):
    __tablename__ = "proposal_items"
    __table_args__ = (UniqueConstraint("proposal_run_id", "stable_key", name="uq_proposal_run_stable_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    proposal_run_id: Mapped[str] = mapped_column(
        ForeignKey("proposal_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stable_key: Mapped[str] = mapped_column(String(160), nullable=False)
    operation: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="READY", index=True)
    target_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    candidate_project_keys_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    proposal_run = relationship("ProposalRun", back_populates="items")
    reviews = relationship("UserReview", back_populates="proposal_item", cascade="all, delete-orphan")
