"""ConversationModel ORM mapping."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from forge.infrastructure.database.base import Base


class ConversationModel(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    state = Column(String(50), nullable=False, server_default="ACTIVE")
    total_token_count = Column(Integer, server_default="0")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    metadata_ = Column(String, server_default="{}", nullable=False)  # Store JSON string

    messages = relationship(
        "MessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="MessageModel.created_at",
    )
    sessions = relationship(
        "ConversationSessionModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationSessionModel.started_at",
    )
    summaries = relationship(
        "ConversationSummaryModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationSummaryModel.created_at",
    )
