from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Integer, Boolean
from forge.infrastructure.database.base import Base

class MemoryModel(Base):
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    memory_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False, default="")
    body = Column(Text, nullable=False, default="")
    source = Column(String(255), nullable=False, default="")
    author = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)
    embedding_reference = Column(String(255), nullable=True)
    version_number = Column(Integer, nullable=False, default=1)
    previous_version_id = Column(String(36), ForeignKey("memories.id"), nullable=True)
    superseded_by_id = Column(String(36), ForeignKey("memories.id"), nullable=True)
    archived_at = Column(DateTime, nullable=True)

    __mapper_args__ = {
        "polymorphic_on": memory_type,
        "polymorphic_identity": "memory",
    }


class BugModel(MemoryModel):
    __tablename__ = "memory_bugs"

    id = Column(String(36), ForeignKey("memories.id"), primary_key=True)
    problem = Column(Text, nullable=False)
    root_cause = Column(Text, default="")
    solution = Column(Text, default="")
    affected_files = Column(JSON, default=list)
    severity = Column(String(50), default="medium")
    resolved = Column(Boolean, default=True)
    resolved_at = Column(DateTime, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "bug",
    }


class DecisionModel(MemoryModel):
    __tablename__ = "memory_decisions"

    id = Column(String(36), ForeignKey("memories.id"), primary_key=True)
    decision = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    alternatives = Column(JSON, default=list)
    status = Column(String(50), default="accepted")

    __mapper_args__ = {
        "polymorphic_identity": "decision",
    }


class FeatureModel(MemoryModel):
    __tablename__ = "memory_features"

    id = Column(String(36), ForeignKey("memories.id"), primary_key=True)
    status = Column(String(50), default="planned")
    acceptance_criteria = Column(JSON, default=list)

    __mapper_args__ = {
        "polymorphic_identity": "feature",
    }


class EngineeringNoteModel(MemoryModel):
    __tablename__ = "memory_notes"

    id = Column(String(36), ForeignKey("memories.id"), primary_key=True)
    tags = Column(JSON, default=list)

    __mapper_args__ = {
        "polymorphic_identity": "note",
    }


class DecisionLogModel(MemoryModel):
    __tablename__ = "memory_decision_logs"

    id = Column(String(36), ForeignKey("memories.id"), primary_key=True)
    decisions_referenced = Column(JSON, default=list)

    __mapper_args__ = {
        "polymorphic_identity": "decision_log",
    }


class EngineeringEventModel(MemoryModel):
    __tablename__ = "memory_events"

    id = Column(String(36), ForeignKey("memories.id"), primary_key=True)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, default=dict)

    __mapper_args__ = {
        "polymorphic_identity": "event",
    }
