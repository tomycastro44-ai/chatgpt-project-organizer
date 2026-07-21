from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AnalysisFinding(Base):
    __tablename__ = "analysis_findings"
    __table_args__ = (UniqueConstraint("run_id", "stable_key", name="uq_analysis_finding_run_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stable_key: Mapped[str] = mapped_column(String(500), nullable=False)
    finding_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    classification: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    confidence: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    chat_id: Mapped[str | None] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), nullable=True, index=True
    )
    related_chat_id: Mapped[str | None] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), nullable=True, index=True
    )
    details_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    run = relationship("AnalysisRun", back_populates="findings")
    chat = relationship("Chat", foreign_keys=[chat_id])
    related_chat = relationship("Chat", foreign_keys=[related_chat_id])
    evidences = relationship(
        "AnalysisEvidence",
        secondary="analysis_finding_evidence",
        back_populates="findings",
        order_by="AnalysisEvidence.precedence, AnalysisEvidence.occurred_at",
    )
