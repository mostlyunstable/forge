"""MessageModel ORM mapping."""

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from forge.infrastructure.database.base import Base


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True)
    conversation_id = Column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, server_default="0")
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, nullable=False)

    conversation = relationship("ConversationModel", back_populates="messages")
    citations = relationship(
        "ConversationCitationModel", back_populates="message", cascade="all, delete-orphan"
    )
