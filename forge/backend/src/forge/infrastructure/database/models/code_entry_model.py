"""CodeEntryModel ORM mapping."""
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, ForeignKey

from forge.infrastructure.database.base import Base


class CodeEntryModel(Base):
    __tablename__ = "code_entries"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    entry_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    content = Column(Text, default="")
    language = Column(String(50), default="")
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    entry_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, nullable=False)
