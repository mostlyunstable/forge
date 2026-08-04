"""IndexJobModel ORM mapping."""

from sqlalchemy import JSON, Column, DateTime, String

from forge.infrastructure.database.base import Base


class IndexJobModel(Base):
    __tablename__ = "index_jobs"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), nullable=False, index=True)
    type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    progress = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    error_log = Column(JSON, default=list)
    checkpoint = Column(JSON, default=dict)
    state_hash = Column(String(64), default="")
    created_by = Column(String(20), default="api")
    created_at = Column(DateTime, nullable=False)
