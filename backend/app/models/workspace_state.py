from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WorkspaceState(Base):
    __tablename__ = "workspace_states"
    __table_args__ = (UniqueConstraint("semantic_run_id", name="uq_workspace_semantic_run"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    semantic_run_id: Mapped[str] = mapped_column(
        ForeignKey("semantic_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    state_json: Mapped[str] = mapped_column(Text, nullable=False)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    semantic_run = relationship("SemanticRun")
