import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.memory.entities.decision import ArchitectureDecision
from forge.domain.memory.entities.note import EngineeringNote
from forge.domain.memory.entities.feature import Feature
from forge.domain.memory.entities.event import EngineeringEvent

from forge.application.memory.use_cases.ingest_adr_usecase import IngestADRUseCase, IngestADRRequest
from forge.application.memory.use_cases.ingest_engineering_note_usecase import IngestEngineeringNoteUseCase, IngestEngineeringNoteRequest
from forge.application.memory.use_cases.create_feature_usecase import CreateFeatureUseCase, CreateFeatureRequest
from forge.application.memory.use_cases.record_engineering_event_usecase import RecordEngineeringEventUseCase, RecordEngineeringEventRequest
from forge.application.memory.use_cases.markdown_parser import parse_markdown

@pytest.fixture
def memory_repo():
    repo = AsyncMock()
    repo.get_by_project.return_value = []
    repo.save.side_effect = lambda x: x
    return repo

@pytest.fixture
def graph_adapter():
    adapter = AsyncMock()
    return adapter

@pytest.fixture
def embedding_service():
    service = AsyncMock()
    service.get_embedding.return_value = [0.1, 0.2, 0.3]
    return service

def test_markdown_parser():
    content = "---\ntitle: Test\ntags: a, b\n---\nBody here"
    meta, body = parse_markdown(content)
    assert meta["title"] == "Test"
    assert meta["tags"] == "a, b"
    assert body == "Body here"

    content2 = "# Hello World\nSome body"
    meta2, body2 = parse_markdown(content2)
    assert meta2["title"] == "Hello World"
    assert body2 == "# Hello World\nSome body"

@pytest.mark.asyncio
async def test_ingest_adr(memory_repo, graph_adapter, embedding_service):
    uc = IngestADRUseCase(memory_repo, graph_adapter, embedding_service)
    req = IngestADRRequest(
        project_id=str(ProjectId()),
        content="---\ntitle: Use Postgres\ndecision: We will use PG\nreason: Scalability\n---\nBody",
        related_files=["db.py"],
        related_commits=["abc1234"]
    )
    result = await uc.execute(req)
    assert isinstance(result, ArchitectureDecision)
    assert result.title == "Use Postgres"
    assert result.decision == "We will use PG"
    assert result.reason == "Scalability"
    assert result.embedding_reference == "embedded"
    
    memory_repo.save.assert_called_once()
    graph_adapter.add_relationships.assert_called_once()
    rel_args = graph_adapter.add_relationships.call_args[0][1]
    assert len(rel_args) == 2
    assert rel_args[0].target_id == "file:db.py"
    assert rel_args[1].target_id == "commit:abc1234"

@pytest.mark.asyncio
async def test_ingest_note(memory_repo, graph_adapter, embedding_service):
    uc = IngestEngineeringNoteUseCase(memory_repo, graph_adapter, embedding_service)
    req = IngestEngineeringNoteRequest(
        project_id=str(ProjectId()),
        content="---\ntitle: Note 1\ntags: tip, trick\n---\nHello",
        related_files=["main.py"]
    )
    result = await uc.execute(req)
    assert isinstance(result, EngineeringNote)
    assert result.title == "Note 1"
    assert result.tags == ["tip", "trick"]
    
    graph_adapter.add_relationships.assert_called_once()

@pytest.mark.asyncio
async def test_create_feature(memory_repo, graph_adapter, embedding_service):
    uc = CreateFeatureUseCase(memory_repo, graph_adapter, embedding_service)
    req = CreateFeatureRequest(
        project_id=str(ProjectId()),
        content="---\ntitle: Login\nacceptance_criteria: Users can log in; Passwords hashed\nstatus: in_progress\n---\nDetails"
    )
    result = await uc.execute(req)
    assert isinstance(result, Feature)
    assert result.title == "Login"
    assert result.status == "in_progress"
    assert result.acceptance_criteria == ["Users can log in", "Passwords hashed"]
    
@pytest.mark.asyncio
async def test_record_event(memory_repo, graph_adapter, embedding_service):
    uc = RecordEngineeringEventUseCase(memory_repo, graph_adapter, embedding_service)
    req = RecordEngineeringEventRequest(
        project_id=str(ProjectId()),
        content="---\ntitle: CI Passed\nevent_type: build\nevent_data: {\"duration\": 10}\n---\nOutput"
    )
    result = await uc.execute(req)
    assert isinstance(result, EngineeringEvent)
    assert result.title == "CI Passed"
    assert result.event_type == "build"
    assert result.event_data == {"duration": 10}
