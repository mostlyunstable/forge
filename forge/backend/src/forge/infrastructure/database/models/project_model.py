"""ProjectModel ORM mapping."""
from sqlalchemy import Column, String, Text, DateTime, JSON

from forge.infrastructure.database.base import Base


class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, default="")
    stack = Column(JSON, default=list)
    goals = Column(JSON, default=list)
    status = Column(String(50), default="active")
    repository_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
