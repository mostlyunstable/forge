"""AnalysisReportModel — SQLAlchemy ORM model for analysis reports."""
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean
from forge.infrastructure.database.base import Base


class AnalysisReportModel(Base):
    """Persisted analysis report."""

    __tablename__ = "analysis_reports"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), nullable=False, index=True)
    pr_number = Column(Integer, nullable=True)
    title = Column(String(500), default="")
    summary = Column(Text, default="")

    # Change set (stored as JSON)
    change_set = Column(JSON, default=dict)

    # Dependency impact (stored as JSON)
    dependency_impact = Column(JSON, default=dict)

    # Historical context (stored as JSON)
    historical_context = Column(JSON, default=dict)

    # Risk assessment (stored as JSON)
    risk_assessment = Column(JSON, default=dict)

    # Recommendations (stored as JSON)
    recommendations = Column(JSON, default=list)

    created_at = Column(DateTime, nullable=False)
