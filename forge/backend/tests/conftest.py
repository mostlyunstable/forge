"""Shared test fixtures and fakes."""
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from forge.domain.projects.entities.project import Project
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.value_objects.tech_stack import TechStack
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.memory.entities.decision import ArchitectureDecision
from forge.domain.memory.value_objects.decision_id import DecisionId
from forge.domain.memory.repository_contracts.decision_repository import IDecisionRepository
from forge.domain.memory.entities.bug import Bug
from forge.domain.memory.value_objects.bug_id import BugId
from forge.domain.memory.repository_contracts.bug_repository import IBugRepository
from forge.domain.memory.entities.preference import DeveloperPreference
from forge.domain.memory.value_objects.preference_key import PreferenceKey
from forge.domain.memory.repository_contracts.preference_repository import IPreferenceRepository
from forge.domain.shared.events import IEventBus, DomainEvent
from forge.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.entities.message import ConversationMessage
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.conversation.repository_contracts.conversation_repository import IConversationRepository
from forge.domain.projects.value_objects.project_id import ProjectId


# --- Fake Repositories ---

class FakeProjectRepo(IProjectRepository):
    def __init__(self):
        self._projects: dict[ProjectId, Project] = {}

    async def save(self, project: Project) -> Project:
        self._projects[project.id] = project
        return project

    async def get_by_id(self, project_id: ProjectId):
        return self._projects.get(project_id)

    async def get_by_name(self, name: str):
        for p in self._projects.values():
            if p.name == name:
                return p
        return None

    async def get_all(self, skip: int = 0, limit: int = 100):
        projects = list(self._projects.values())
        return projects[skip:skip + limit]

    async def delete(self, project_id: ProjectId) -> bool:
        if project_id in self._projects:
            del self._projects[project_id]
            return True
        return False

    async def search_by_name(self, query: str):
        return [p for p in self._projects.values() if query.lower() in p.name.lower()]


class FakeDecisionRepo(IDecisionRepository):
    def __init__(self):
        self._decisions: dict[DecisionId, ArchitectureDecision] = {}

    async def save(self, decision: ArchitectureDecision) -> ArchitectureDecision:
        self._decisions[decision.id] = decision
        return decision

    async def get_by_id(self, decision_id: DecisionId):
        return self._decisions.get(decision_id)

    async def get_by_project(self, project_id):
        return [d for d in self._decisions.values() if d.project_id == project_id]

    async def delete(self, decision_id: DecisionId) -> bool:
        if decision_id in self._decisions:
            del self._decisions[decision_id]
            return True
        return False

    async def search_by_title(self, query: str):
        return [d for d in self._decisions.values() if query.lower() in d.title.lower()]


class FakeBugRepo(IBugRepository):
    def __init__(self):
        self._bugs: dict[BugId, Bug] = {}

    async def save(self, bug: Bug) -> Bug:
        self._bugs[bug.id] = bug
        return bug

    async def get_by_id(self, bug_id: BugId):
        return self._bugs.get(bug_id)

    async def get_by_project(self, project_id):
        return [b for b in self._bugs.values() if b.project_id == project_id]

    async def get_unresolved(self, project_id):
        return [b for b in self._bugs.values() if b.project_id == project_id and not b.resolved]

    async def delete(self, bug_id: BugId) -> bool:
        if bug_id in self._bugs:
            del self._bugs[bug_id]
            return True
        return False

    async def search_by_problem(self, query: str):
        return [b for b in self._bugs.values() if query.lower() in b.problem.lower()]


class FakeConversationRepo(IConversationRepository):
    def __init__(self):
        self._conversations: dict[ConversationId, Conversation] = {}

    async def save(self, conversation: Conversation) -> Conversation:
        self._conversations[conversation.id] = conversation
        return conversation

    async def get_by_id(self, conversation_id: ConversationId):
        return self._conversations.get(conversation_id)

    async def get_by_project(self, project_id: ProjectId, skip: int = 0, limit: int = 50):
        convs = [
            c for c in self._conversations.values()
            if c.project_id == project_id
        ]
        convs.sort(key=lambda c: c.updated_at, reverse=True)
        return convs[skip:skip + limit]

    async def delete(self, conversation_id: ConversationId) -> bool:
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    async def search(self, project_id: ProjectId, query: str):
        return [
            c for c in self._conversations.values()
            if c.project_id == project_id
            and (query.lower() in c.title.lower() or any(query.lower() in s.content.lower() for s in c.summaries))
        ]

    async def count_by_project(self, project_id: ProjectId) -> int:
        return sum(
            1 for c in self._conversations.values()
            if c.project_id == project_id
        )


class FakePreferenceRepo(IPreferenceRepository):
    def __init__(self):
        self._prefs: dict[PreferenceKey, DeveloperPreference] = {}

    async def save(self, preference: DeveloperPreference) -> DeveloperPreference:
        self._prefs[preference.key] = preference
        return preference

    async def get_by_key(self, key: PreferenceKey):
        return self._prefs.get(key)

    async def get_all(self, skip: int = 0, limit: int = 100):
        prefs = list(self._prefs.values())
        return prefs[skip:skip + limit]

    async def delete(self, key: PreferenceKey) -> bool:
        if key in self._prefs:
            del self._prefs[key]
            return True
        return False


# --- Fake Event Bus ---

class FakeEventBus(InMemoryEventBus):
    """Event bus for testing that records all events."""
    pass


# --- Fixtures ---

@pytest.fixture
def project_repo():
    return FakeProjectRepo()


@pytest.fixture
def decision_repo():
    return FakeDecisionRepo()


@pytest.fixture
def bug_repo():
    return FakeBugRepo()


@pytest.fixture
def preference_repo():
    return FakePreferenceRepo()


@pytest.fixture
def event_bus():
    return FakeEventBus()


@pytest.fixture
def sample_project(project_repo):
    project = Project.create(
        name="Test Project",
        description="A test project",
        stack=TechStack.from_list(["python", "fastapi"]),
        goals=["Test goal"],
    )
    project_repo._projects[project.id] = project
    return project


@pytest.fixture
def sample_decision(decision_repo, sample_project):
    decision = ArchitectureDecision.create(
        project_id=sample_project.id,
        title="Use FastAPI",
        decision="Use FastAPI for the API",
        reason="It's fast and modern",
        alternatives=["Django", "Flask"],
    )
    decision_repo._decisions[decision.id] = decision
    return decision


@pytest.fixture
def sample_bug(bug_repo, sample_project):
    bug = Bug.create(
        project_id=sample_project.id,
        title="Null pointer",
        problem="App crashes on null input",
        root_cause="Missing validation",
        solution="Add null check",
        severity="high",
    )
    bug_repo._bugs[bug.id] = bug
    return bug


@pytest.fixture
def sample_preference(preference_repo):
    pref = DeveloperPreference.create(
        key="code_style",
        value="black",
        confidence=0.8,
    )
    preference_repo._prefs[pref.key] = pref
    return pref


@pytest.fixture
def conversation_repo():
    return FakeConversationRepo()


@pytest.fixture
def sample_conversation(conversation_repo, sample_project):
    conv = Conversation.create(
        project_id=sample_project.id,
        title="Debugging session",
    )
    conversation_repo._conversations[conv.id] = conv
    return conv
