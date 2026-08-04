"""PreferenceModel ORM mapping."""

from sqlalchemy import Column, DateTime, Float, Integer, String

from forge.infrastructure.database.base import Base


class PreferenceModel(Base):
    __tablename__ = "developer_preferences"

    id = Column(String(255), primary_key=True)  # preference_key as ID
    value = Column(String(500), nullable=False)
    confidence = Column(Float, default=0.5)
    evidence_count = Column(Integer, default=1)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
