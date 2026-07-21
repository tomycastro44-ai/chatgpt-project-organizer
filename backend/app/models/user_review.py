from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserReview(Base):
    __tablename__ = "user_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    proposal_run_id: Mapped[str] = mapped_column(
        ForeignKey("proposal_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proposal_item_id: Mapped[str] = mapped_column(
        ForeignKey("proposal_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    correction_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    proposal_run = relationship("ProposalRun", back_populates="reviews")
    proposal_item = relationship("ProposalItem", back_populates="reviews")
