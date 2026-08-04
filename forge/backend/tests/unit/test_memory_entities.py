from dataclasses import FrozenInstanceError

import pytest

from forge.domain.memory.entities.bug import Bug
from forge.domain.memory.entities.decision import ArchitectureDecision
from forge.domain.memory.entities.decision_log import DecisionLog
from forge.domain.memory.entities.event import EngineeringEvent
from forge.domain.memory.entities.feature import Feature
from forge.domain.memory.entities.memory import Memory
from forge.domain.memory.entities.note import EngineeringNote
from forge.domain.memory.value_objects.memory_id import MemoryId
from forge.domain.projects.value_objects.project_id import ProjectId


def test_bug_creation_and_inheritance():
    pid = ProjectId()
    bug = Bug.create(
        project_id=pid,
        title="Test Bug",
        problem="Crash",
        root_cause="Null ptr",
        solution="Check null",
    )
    assert isinstance(bug, Memory)
    assert bug.memory_type == "bug"
    assert bug.title == "Test Bug"
    assert bug.problem == "Crash"
    assert bug.resolved is True

    # Test update_content inherited from Memory
    bug.update_content(title="New Title", summary="New sum", body="New body")
    assert bug.title == "New Title"
    assert bug.summary == "New sum"

    # Test archiving
    assert bug.archived_at is None
    bug.archive()
    assert bug.archived_at is not None


def test_architecture_decision_creation():
    pid = ProjectId()
    decision = ArchitectureDecision.create(
        project_id=pid,
        title="Use PostgreSQL",
        decision="Use PG",
        reason="Good",
        alternatives=["MySQL"],
    )
    assert isinstance(decision, Memory)
    assert decision.memory_type == "decision"
    decision.add_alternative("SQLite")
    assert "SQLite" in decision.alternatives


def test_feature_creation():
    pid = ProjectId()
    feature = Feature.create(
        project_id=pid,
        title="Login system",
        status="in_progress",
        acceptance_criteria=["User can login"],
    )
    assert isinstance(feature, Memory)
    assert feature.memory_type == "feature"
    assert feature.status == "in_progress"


def test_engineering_note_creation():
    pid = ProjectId()
    note = EngineeringNote.create(
        project_id=pid, title="Meeting notes", tags=["meeting", "architecture"]
    )
    assert isinstance(note, Memory)
    assert note.memory_type == "note"
    assert note.tags == ["meeting", "architecture"]


def test_decision_log_creation():
    pid = ProjectId()
    mid = MemoryId()
    log = DecisionLog.create(project_id=pid, title="Q3 Decisions", decisions_referenced=[mid])
    assert isinstance(log, Memory)
    assert log.memory_type == "decision_log"
    assert mid in log.decisions_referenced


def test_engineering_event_is_immutable():
    pid = ProjectId()
    event = EngineeringEvent.create(
        project_id=pid,
        title="System Deployment",
        event_type="deployment",
        event_data={"version": "1.0.0"},
    )
    assert isinstance(event, Memory)
    assert event.memory_type == "event"
    assert event.event_type == "deployment"

    with pytest.raises(FrozenInstanceError):
        event.title = "New Title"

    with pytest.raises(FrozenInstanceError):
        event.update_content("Title", "Sum", "Body")

    with pytest.raises(FrozenInstanceError):
        event.archive()

    with pytest.raises(FrozenInstanceError):
        event.event_data = {}
