"""Unit tests for Memory versioning and archiving use cases."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from copy import deepcopy

from forge.domain.memory.value_objects.memory_id import MemoryId
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.memory.entities.note import EngineeringNote
from forge.domain.memory.exceptions import MemoryNotFoundError

from forge.application.memory.use_cases.archive_memory_usecase import (
    ArchiveMemoryUseCase,
    ArchiveMemoryRequest,
)
from forge.application.memory.use_cases.update_memory_usecase import (
    UpdateMemoryUseCase,
    UpdateMemoryRequest,
)
from forge.application.memory.use_cases.search_knowledge_usecase import (
    SearchKnowledgeUseCase,
    SearchKnowledgeRequest,
)


@pytest.fixture
def memory_repo_mock():
    repo = AsyncMock()
    return repo


@pytest.fixture
def sample_note():
    note = EngineeringNote(
        id=MemoryId(),
        project_id=ProjectId(),
        memory_type="note",
        title="Original Title",
        summary="Original Summary",
        body="Original Body",
        source="test",
        author="test_author",
        tags=["test"]
    )
    return note


class TestArchiveMemoryUseCase:
    @pytest.mark.asyncio
    async def test_archive_memory_success(self, memory_repo_mock, sample_note):
        memory_repo_mock.get_by_id.return_value = sample_note
        
        use_case = ArchiveMemoryUseCase(memory_repo_mock)
        request = ArchiveMemoryRequest(memory_id=str(sample_note.id.value))
        
        response = await use_case.execute(request)
        
        assert response.success is True
        assert response.memory_id == str(sample_note.id.value)
        assert sample_note.archived_at is not None
        memory_repo_mock.save.assert_called_once_with(sample_note)

    @pytest.mark.asyncio
    async def test_archive_memory_not_found(self, memory_repo_mock):
        memory_repo_mock.get_by_id.return_value = None
        
        use_case = ArchiveMemoryUseCase(memory_repo_mock)
        request = ArchiveMemoryRequest(memory_id=str(MemoryId().value))
        
        with pytest.raises(MemoryNotFoundError):
            await use_case.execute(request)


class TestUpdateMemoryUseCase:
    @pytest.mark.asyncio
    async def test_update_memory_creates_new_version(self, memory_repo_mock, sample_note):
        memory_repo_mock.get_by_id.return_value = sample_note
        
        use_case = UpdateMemoryUseCase(memory_repo_mock)
        request = UpdateMemoryRequest(
            memory_id=str(sample_note.id.value),
            title="New Title",
            summary="New Summary"
        )
        
        response = await use_case.execute(request)
        
        # Verify repo calls
        assert memory_repo_mock.save.call_count == 2
        
        # Original memory should be superseded
        assert sample_note.superseded_by_id is not None
        assert str(sample_note.superseded_by_id.value) == response.memory_id
        
        assert response.previous_version_id == str(sample_note.id.value)
        assert response.version_number == 2


class TestSearchKnowledgeUseCase:
    @pytest.mark.asyncio
    async def test_search_knowledge_matches(self, memory_repo_mock, sample_note):
        # Create another note that shouldn't match
        other_note = deepcopy(sample_note)
        other_note.id = MemoryId()
        other_note.title = "Unrelated Topic"
        other_note.summary = "Unrelated"
        other_note.body = "Unrelated"
        
        memory_repo_mock.get_by_project.return_value = [sample_note, other_note]
        
        use_case = SearchKnowledgeUseCase(memory_repo_mock)
        request = SearchKnowledgeRequest(
            project_id=str(sample_note.project_id.value),
            query="original",
            limit=10
        )
        
        response = await use_case.execute(request)
        
        assert len(response.results) == 1
        assert response.results[0].id == str(sample_note.id.value)
        assert response.query == "original"

    @pytest.mark.asyncio
    async def test_search_knowledge_ignores_archived_and_superseded(self, memory_repo_mock, sample_note):
        archived_note = deepcopy(sample_note)
        archived_note.id = MemoryId()
        archived_note.archive()
        
        superseded_note = deepcopy(sample_note)
        superseded_note.id = MemoryId()
        superseded_note.superseded_by_id = MemoryId()
        
        memory_repo_mock.get_by_project.return_value = [sample_note, archived_note, superseded_note]
        
        use_case = SearchKnowledgeUseCase(memory_repo_mock)
        request = SearchKnowledgeRequest(
            project_id=str(sample_note.project_id.value),
            query="original",
            limit=10
        )
        
        response = await use_case.execute(request)
        
        # Only the active one should be returned
        assert len(response.results) == 1
        assert response.results[0].id == str(sample_note.id.value)
