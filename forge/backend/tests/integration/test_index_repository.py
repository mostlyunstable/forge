"""Integration tests for code indexing use case."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from forge.domain.projects.entities.project import Project
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.value_objects.tech_stack import TechStack
from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.code.repository_contracts.code_repository import ICodeRepository
from forge.application.code.index_repository import IndexRepositoryUseCase, IndexRepositoryRequest
from forge.domain.code.value_objects.entry_type import EntryType


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
        return list(self._projects.values())[skip:skip+limit]

    async def delete(self, project_id):
        if project_id in self._projects:
            del self._projects[project_id]
            return True
        return False

    async def search_by_name(self, query):
        return [p for p in self._projects.values() if query.lower() in p.name.lower()]


class FakeCodeRepo(ICodeRepository):
    def __init__(self):
        self._entries = []

    async def save(self, entry):
        self._entries.append(entry)
        return entry

    async def get_by_id(self, entry_id):
        for e in self._entries:
            if e.id == entry_id:
                return e
        return None

    async def get_by_project(self, project_id):
        return [e for e in self._entries if e.project_id == project_id]

    async def get_by_file_path(self, project_id, file_path):
        return [e for e in self._entries if e.project_id == project_id and e.file_path.value == file_path]

    async def get_by_type(self, project_id, entry_type):
        return [e for e in self._entries if e.project_id == project_id and e.entry_type == entry_type]

    async def save_many(self, entries):
        self._entries.extend(entries)
        return entries

    async def delete_by_project(self, project_id):
        self._entries = [e for e in self._entries if e.project_id != project_id]
        return True

    async def search_by_name(self, project_id, query):
        return [e for e in self._entries if e.project_id == project_id and query.lower() in e.name.lower()]


class FakeCodeIndexer:
    def __init__(self):
        self._indexed = []

    async def index(self, project_id, repo_path):
        from forge.domain.code.entities.code_entry import CodeEntry
        entry = CodeEntry.create(
            project_id=project_id,
            file_path="src/main.py",
            entry_type=EntryType.FUNCTION,
            name="main",
            content="def main(): pass",
            language="python",
            start_line=1,
            end_line=2,
        )
        self._indexed.append(entry)
        return [entry]


@pytest.mark.asyncio
async def test_index_repository_use_case():
    project_repo = FakeProjectRepo()
    code_repo = FakeCodeRepo()
    code_indexer = FakeCodeIndexer()

    project_id = ProjectId(uuid4())
    project = Project.create(
        name="Test",
        description="T",
        stack=TechStack.from_list(["python"]),
        goals=[],
    )
    project._id = project_id
    project_repo._projects[project_id] = project

    use_case = IndexRepositoryUseCase(project_repo, code_repo, code_indexer)
    result = await use_case.execute(
        IndexRepositoryRequest(
            project_id=str(project_id.value),
            repo_path="/test/repo",
        )
    )

    assert result.files_indexed >= 1
    assert result.entries_found == 1


@pytest.mark.asyncio
async def test_index_repository_project_not_found():
    project_repo = FakeProjectRepo()
    code_repo = FakeCodeRepo()
    code_indexer = FakeCodeIndexer()

    use_case = IndexRepositoryUseCase(project_repo, code_repo, code_indexer)

    with pytest.raises(Exception):
        await use_case.execute(
            IndexRepositoryRequest(
                project_id=str(uuid4()),
                repo_path="/test/repo",
            )
        )
