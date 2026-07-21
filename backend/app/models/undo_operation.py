from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UndoOperation(Base):
    __tablename__ = "undo_operations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    applied_operation_id: Mapped[str] = mapped_column(
        ForeignKey("applied_operations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="COMPLETED", index=True)
    restored_state_json: Mapped[str] = mapped_column(Text, nullable=False)
    restored_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    audit_history_preserved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    originals_modified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    applied_operation = relationship("AppliedOperation", back_populates="undo_operations")
