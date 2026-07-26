"""ConversationSummaryModel ORM mapping."""
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship

from forge.infrastructure.database.base import Base


class ConversationSummaryModel(Base):
    __tablename__ = "conversation_summaries"

    id = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, server_default="0")
    created_at = Column(DateTime, nullable=False)

    conversation = relationship("ConversationModel", back_populates="summaries")
