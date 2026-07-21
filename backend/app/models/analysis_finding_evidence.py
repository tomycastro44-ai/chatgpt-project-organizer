from sqlalchemy import Column, ForeignKey, Table

from app.core.database import Base


analysis_finding_evidence = Table(
    "analysis_finding_evidence",
    Base.metadata,
    Column("finding_id", ForeignKey("analysis_findings.id", ondelete="CASCADE"), primary_key=True),
    Column("evidence_id", ForeignKey("analysis_evidence.id", ondelete="CASCADE"), primary_key=True),
)
