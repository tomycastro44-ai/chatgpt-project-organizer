from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SemanticException(Base):
    __tablename__ = "semantic_exceptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    semantic_run_id: Mapped[str] = mapped_column(
        ForeignKey("semantic_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chat_id: Mapped[str | None] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    confidence: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    candidate_project_keys_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    semantic_run = relationship("SemanticRun", back_populates="exceptions")
    chat = relationship("Chat")
