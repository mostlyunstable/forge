"""BugModel ORM mapping."""
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, ForeignKey

from forge.infrastructure.database.base import Base


class BugModel(Base):
    __tablename__ = "bugs"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    problem = Column(Text, nullable=False)
    root_cause = Column(Text, default="")
    solution = Column(Text, default="")
    affected_files = Column(JSON, default=list)
    severity = Column(String(50), default="medium")
    resolved = Column(Boolean, default=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
