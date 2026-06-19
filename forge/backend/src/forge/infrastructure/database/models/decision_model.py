"""DecisionModel ORM mapping."""
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey

from forge.infrastructure.database.base import Base


class DecisionModel(Base):
    __tablename__ = "architecture_decisions"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    decision = Column(Text, nullable=False)
    reason = Column(Text, default="")
    alternatives = Column(JSON, default=list)
    status = Column(String(50), default="accepted")
    created_at = Column(DateTime, nullable=False)
