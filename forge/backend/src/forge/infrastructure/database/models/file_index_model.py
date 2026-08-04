"""FileIndexModel ORM mapping."""

from sqlalchemy import Column, DateTime, String, Text

from forge.infrastructure.database.base import Base


class FileIndexModel(Base):
    __tablename__ = "file_indices"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    language = Column(String(50), default="")
    last_indexed_commit = Column(String(40), default="")
    parsed_at = Column(DateTime, nullable=False)
    index_job_id = Column(String(36), nullable=True)
