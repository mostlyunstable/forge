"""CommitModel ORM mapping."""
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey

from forge.infrastructure.database.base import Base


class CommitModel(Base):
    __tablename__ = "commits"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    sha = Column(String(40), nullable=False)
    message = Column(Text, nullable=False)
    author = Column(String(255), default="")
    timestamp = Column(DateTime, nullable=False)
    files_changed = Column(JSON, default=list)
    classification = Column(String(50), default="other")
    summary = Column(Text, default="")
    created_at = Column(DateTime, nullable=False)
