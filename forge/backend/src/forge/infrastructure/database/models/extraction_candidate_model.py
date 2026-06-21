"""ExtractionCandidateModel ORM mapping."""
from sqlalchemy import Column, String, DateTime, JSON, Float, Text

from forge.infrastructure.database.base import Base


class ExtractionCandidateModel(Base):
    __tablename__ = "extraction_candidates"

    id = Column(String(36), primary_key=True)
    job_id = Column(String(36), nullable=False, index=True)
    kind = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="suggested")
    data = Column(JSON, default=dict)
    source_commit = Column(String(40), default="")
    source_file = Column(Text, default="")
    dedup_key = Column(String(64), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
