"""Unit tests for domain entities."""

from uuid import uuid4

from forge.domain.code.entities.code_entry import CodeEntry
from forge.domain.code.value_objects.code_location import LineRange
from forge.domain.code.value_objects.entry_type import EntryType
from forge.domain.memory.entities.bug import Bug
from forge.domain.memory.entities.decision import ArchitectureDecision
from forge.domain.memory.value_objects.bug_id import BugId
from forge.domain.memory.value_objects.decision_id import DecisionId
from forge.domain.projects.entities.project import Project
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.value_objects.tech_stack import TechStack


def test_project_create():
    project = Project.create(
        name="Test Project",
        description="A test",
        stack=TechStack.from_list(["python", "fastapi"]),
        goals=["Goal 1"],
    )
    assert project.name == "Test Project"
    assert project.description == "A test"
    assert project.goals == ["Goal 1"]
    assert isinstance(project.id, ProjectId)


def test_project_add_goal():
    project = Project.create(name="Test", description="T", stack=TechStack(), goals=[])
    project.add_goal("Goal")
    assert "Goal" in project.goals
    # Adding same goal again should not duplicate
    project.add_goal("Goal")
    assert project.goals.count("Goal") == 1


def test_decision_create():
    decision = ArchitectureDecision.create(
        project_id=ProjectId(uuid4()),
        title="Use FastAPI",
        decision="We chose FastAPI",
        reason="Performance",
        alternatives=["Flask", "Django"],
    )
    assert decision.title == "Use FastAPI"
    assert decision.decision == "We chose FastAPI"
    assert decision.reason == "Performance"
    assert decision.alternatives == ["Flask", "Django"]
    assert isinstance(decision.id, DecisionId)


def test_bug_create():
    bug = Bug.create(
        project_id=ProjectId(uuid4()),
        title="Auth bug",
        problem="Login fails",
        root_cause="Token expired",
        solution="Refresh token",
        affected_files=["auth.py"],
        severity="high",
    )
    assert bug.title == "Auth bug"
    assert bug.resolved is True
    assert bug.severity == "high"
    assert isinstance(bug.id, BugId)


def test_code_entry_create():
    entry = CodeEntry.create(
        project_id=ProjectId(uuid4()),
        file_path="src/main.py",
        entry_type=EntryType.FUNCTION,
        name="main",
        content="def main(): pass",
        language="python",
        start_line=1,
        end_line=3,
        metadata={},
    )
    assert entry.name == "main"
    assert entry.entry_type == EntryType.FUNCTION
    assert entry.file_path.value == "src/main.py"


def test_line_range_validation():
    lr = LineRange(start=10, end=20)
    assert lr.start == 10
    assert lr.end == 20
