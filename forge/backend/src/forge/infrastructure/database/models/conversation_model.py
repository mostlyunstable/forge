"""ConversationModel ORM mapping."""
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, ForeignKey

from forge.infrastructure.database.base import Base


class ConversationModel(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, server_default="")
    summary_token_count = Column(Integer, server_default="0")
    total_token_count = Column(Integer, server_default="0")
    message_count = Column(Integer, server_default="0")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
