"""ConversationCitationModel ORM mapping."""
from sqlalchemy import Column, String, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from forge.infrastructure.database.base import Base


class ConversationCitationModel(Base):
    __tablename__ = "conversation_citations"

    id = Column(String(36), primary_key=True)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)
    source_reference = Column(String(255), nullable=False)
    snippet = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    message = relationship("MessageModel", back_populates="citations")
