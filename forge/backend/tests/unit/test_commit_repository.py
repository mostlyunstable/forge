import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from forge.domain.git.entities.commit import Commit
from forge.domain.git.value_objects.commit_classification import CommitClassification
from forge.domain.git.value_objects.commit_sha import CommitSha
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure.database.models.commit_model import CommitModel
from forge.infrastructure.repositories.commit_repository import CommitRepository


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    return session


@pytest.fixture
def repository(mock_session):
    return CommitRepository(mock_session)


@pytest.fixture
def sample_commit():
    return Commit(
        project_id=ProjectId(uuid.uuid4()),
        sha=CommitSha("a1b2c3d4e5f6"),
        message="test commit",
        author="Author",
        timestamp=datetime.now(),
        files_changed=["file.py"],
        classification=CommitClassification.FEATURE,
        summary="A summary",
    )


def create_mock_model(commit: Commit):
    model = CommitModel(
        project_id=str(commit.project_id.value),
        sha=commit.sha.value,
        message=commit.message,
        author=commit.author,
        timestamp=commit.timestamp,
        files_changed=commit.files_changed,
        classification=commit.classification.value,
        summary=commit.summary,
        created_at=commit.created_at,
    )
    return model


@pytest.mark.asyncio
async def test_get_by_sha_found(repository, mock_session, sample_commit):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = create_mock_model(sample_commit)
    mock_session.execute.return_value = mock_result

    result = await repository.get_by_sha(sample_commit.project_id, sample_commit.sha)
    assert result is not None
    assert result.sha.value == sample_commit.sha.value


@pytest.mark.asyncio
async def test_get_by_sha_not_found(repository, mock_session, sample_commit):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await repository.get_by_sha(sample_commit.project_id, sample_commit.sha)
    assert result is None


@pytest.mark.asyncio
async def test_get_by_project(repository, mock_session, sample_commit):
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [create_mock_model(sample_commit)]
    mock_session.execute.return_value = mock_result

    result = await repository.get_by_project(sample_commit.project_id)
    assert len(result) == 1
    assert result[0].sha.value == sample_commit.sha.value


@pytest.mark.asyncio
async def test_get_by_classification(repository, mock_session, sample_commit):
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [create_mock_model(sample_commit)]
    mock_session.execute.return_value = mock_result

    result = await repository.get_by_classification(
        sample_commit.project_id, CommitClassification.FEATURE
    )
    assert len(result) == 1
    assert result[0].classification == CommitClassification.FEATURE


@pytest.mark.asyncio
async def test_get_recent(repository, mock_session, sample_commit):
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [create_mock_model(sample_commit)]
    mock_session.execute.return_value = mock_result

    result = await repository.get_recent(sample_commit.project_id, limit=5)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_save_new(repository, mock_session, sample_commit):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await repository.save(sample_commit)
    assert result.sha.value == sample_commit.sha.value
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_save_existing(repository, mock_session, sample_commit):
    existing_model = create_mock_model(sample_commit)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_model
    mock_session.execute.return_value = mock_result

    # Modify the commit to trigger an update
    sample_commit.message = "Updated message"

    result = await repository.save(sample_commit)

    assert existing_model.message == "Updated message"
    assert result.message == "Updated message"
    mock_session.add.assert_not_called()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_save_many(repository, mock_session, sample_commit):
    commits = [sample_commit]

    result = await repository.save_many(commits)

    assert len(result) == 1
    mock_session.add_all.assert_called_once()
    mock_session.flush.assert_called_once()
