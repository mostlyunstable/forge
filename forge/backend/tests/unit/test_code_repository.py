import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from forge.domain.code.entities.code_entry import CodeEntry
from forge.domain.code.value_objects.code_location import FilePath, LineRange
from forge.domain.code.value_objects.entry_type import EntryType
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure.database.models.code_entry_model import CodeEntryModel
from forge.infrastructure.repositories.code_repository import CodeRepository


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add_all = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    return CodeRepository(mock_session)


@pytest.fixture
def sample_code_entry():
    return CodeEntry(
        id=uuid.uuid4(),
        project_id=ProjectId(uuid.uuid4()),
        file_path=FilePath("src/main.py"),
        entry_type=EntryType.CLASS,
        name="MainClass",
        content="class MainClass:\n    pass",
        language="python",
        lines=LineRange(start=1, end=2),
        metadata={"key": "value"},
        created_at=datetime.now(),
    )


def create_mock_model(entry: CodeEntry):
    return CodeEntryModel(
        id=str(entry.id),
        project_id=str(entry.project_id.value),
        file_path=str(entry.file_path),
        entry_type=entry.entry_type.value,
        name=entry.name,
        content=entry.content,
        language=entry.language,
        start_line=entry.lines.start,
        end_line=entry.lines.end,
        metadata=entry.metadata,
        created_at=entry.created_at,
    )


@pytest.mark.asyncio
async def test_get_by_id_found(repository, mock_session, sample_code_entry):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = create_mock_model(sample_code_entry)
    mock_session.execute.return_value = mock_result

    result = await repository.get_by_id(sample_code_entry.id)
    assert result is not None
    assert result.id == sample_code_entry.id


@pytest.mark.asyncio
async def test_get_by_id_not_found(repository, mock_session, sample_code_entry):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await repository.get_by_id(sample_code_entry.id)
    assert result is None


@pytest.mark.asyncio
async def test_get_by_project(repository, mock_session, sample_code_entry):
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [create_mock_model(sample_code_entry)]
    mock_session.execute.return_value = mock_result

    result = await repository.get_by_project(sample_code_entry.project_id)
    assert len(result) == 1
    assert result[0].id == sample_code_entry.id


@pytest.mark.asyncio
async def test_get_by_file_path(repository, mock_session, sample_code_entry):
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [create_mock_model(sample_code_entry)]
    mock_session.execute.return_value = mock_result

    result = await repository.get_by_file_path(sample_code_entry.project_id, "src/main.py")
    assert len(result) == 1
    assert result[0].file_path.value == "src/main.py"


@pytest.mark.asyncio
async def test_get_by_type(repository, mock_session, sample_code_entry):
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [create_mock_model(sample_code_entry)]
    mock_session.execute.return_value = mock_result

    result = await repository.get_by_type(sample_code_entry.project_id, EntryType.CLASS)
    assert len(result) == 1
    assert result[0].entry_type == EntryType.CLASS


@pytest.mark.asyncio
async def test_save_many(repository, mock_session, sample_code_entry):
    result = await repository.save_many([sample_code_entry])
    assert len(result) == 1
    assert result[0].id == sample_code_entry.id
    mock_session.add_all.assert_called_once()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_delete_by_project(repository, mock_session, sample_code_entry):
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [create_mock_model(sample_code_entry)]
    mock_session.execute.return_value = mock_result

    result = await repository.delete_by_project(sample_code_entry.project_id)
    assert result is True
    mock_session.delete.assert_called_once()


@pytest.mark.asyncio
async def test_search_by_name(repository, mock_session, sample_code_entry):
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [create_mock_model(sample_code_entry)]
    mock_session.execute.return_value = mock_result

    result = await repository.search_by_name(sample_code_entry.project_id, "Main")
    assert len(result) == 1
    assert result[0].name == "MainClass"
