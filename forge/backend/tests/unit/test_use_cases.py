"""Unit tests for application use cases."""

from uuid import uuid4

import pytest

from forge.application.memory.save_decision import SaveDecisionRequest, SaveDecisionUseCase
from forge.application.projects.create_project import CreateProjectRequest, CreateProjectUseCase
from forge.application.projects.list_projects import ListProjectsUseCase
from forge.domain.memory.repository_contracts.decision_repository import IDecisionRepository
from forge.domain.projects.entities.project import Project
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.value_objects.tech_stack import TechStack


class FakeProjectRepo(IProjectRepository):
    def __init__(self):
        self._projects = {}

    async def save(self, project):
        self._projects[project.id] = project
        return project

    async def get_by_id(self, project_id):
        return self._projects.get(project_id)

    async def get_by_name(self, name):
        for p in self._projects.values():
            if p.name == name:
                return p
        return None

    async def get_all(self, skip=0, limit=100):
        projects = list(self._projects.values())
        return projects[skip : skip + limit]

    async def delete(self, project_id):
        if project_id in self._projects:
            del self._projects[project_id]
            return True
        return False

    async def search_by_name(self, query):
        return [p for p in self._projects.values() if query.lower() in p.name.lower()]


class FakeDecisionRepo(IDecisionRepository):
    def __init__(self):
        self._decisions = {}

    async def save(self, decision):
        self._decisions[decision.id] = decision
        return decision

    async def get_by_id(self, decision_id):
        return self._decisions.get(decision_id)

    async def get_by_project(self, project_id):
        return [d for d in self._decisions.values() if d.project_id == project_id]

    async def delete(self, decision_id):
        if decision_id in self._decisions:
            del self._decisions[decision_id]
            return True
        return False

    async def search_by_title(self, query):
        return [d for d in self._decisions.values() if query.lower() in d.title.lower()]


@pytest.mark.asyncio
async def test_create_project_use_case():
    repo = FakeProjectRepo()
    use_case = CreateProjectUseCase(repo)
    result = await use_case.execute(
        CreateProjectRequest(
            name="Test",
            description="Test desc",
            stack=TechStack.from_list(["python"]),
            goals=["Goal"],
        )
    )
    assert result.name == "Test"
    assert result.description == "Test desc"


@pytest.mark.asyncio
async def test_list_projects_use_case():
    repo = FakeProjectRepo()
    use_case = ListProjectsUseCase(repo)
    result = await use_case.execute(skip=0, limit=10)
    assert result.projects == []
    assert result.total == 0


@pytest.mark.asyncio
async def test_save_decision_use_case():
    decision_repo = FakeDecisionRepo()
    project_repo = FakeProjectRepo()
    use_case = SaveDecisionUseCase(decision_repo, project_repo)
    project_id = ProjectId(uuid4())
    project = Project.create(
        name="Test",
        description="T",
        stack=TechStack.from_list(["python"]),
        goals=[],
    )
    project._id = project_id
    project_repo._projects[project_id] = project
    result = await use_case.execute(
        SaveDecisionRequest(
            project_id=str(project_id.value),
            title="Test Decision",
            decision="Do X",
            reason="Because",
            alternatives=["Y", "Z"],
        )
    )
    assert result.title == "Test Decision"
