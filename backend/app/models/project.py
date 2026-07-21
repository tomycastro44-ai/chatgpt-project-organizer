from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("semantic_run_id", "project_key", name="uq_project_run_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    semantic_run_id: Mapped[str] = mapped_column(
        ForeignKey("semantic_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    confidence: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    current_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    previous_versions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    discarded_versions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    phase: Mapped[str | None] = mapped_column(String(500), nullable=True)
    approved_decisions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    superseded_decisions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    discarded_items_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    pending_tasks_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    blockers_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    last_confirmed_advance: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_probable_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    semantic_run = relationship("SemanticRun", back_populates="projects")
    memberships = relationship("ProjectMembership", back_populates="project", cascade="all, delete-orphan")
    evidences = relationship("ProjectEvidence", back_populates="project", cascade="all, delete-orphan")
