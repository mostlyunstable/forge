"""ConversationSessionModel ORM mapping."""
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from forge.infrastructure.database.base import Base


class ConversationSessionModel(Base):
    __tablename__ = "conversation_sessions"

    id = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    conversation = relationship("ConversationModel", back_populates="sessions")
