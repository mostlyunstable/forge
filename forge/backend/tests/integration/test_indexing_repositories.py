"""Integration tests for indexing repositories."""
import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from forge.infrastructure.database.base import Base
from forge.domain.indexing.entities.index_job import IndexJob
from forge.domain.indexing.entities.file_index import FileIndex
from forge.domain.indexing.entities.extraction_candidate import ExtractionCandidate
from forge.domain.indexing.value_objects.index_type import IndexType
from forge.infrastructure.indexing.index_job_repository import IndexJobRepository
from forge.infrastructure.indexing.file_index_repository import FileIndexRepository
from forge.infrastructure.indexing.extraction_candidate_repository import (
    ExtractionCandidateRepository,
)


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


class TestIndexJobRepository:
    @pytest.mark.asyncio
    async def test_save_and_get(self, session):
        repo = IndexJobRepository(session)
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        await repo.save(job)

        fetched = await repo.get_by_id(job.id)
        assert fetched is not None
        assert fetched.id == job.id
        assert fetched.type == IndexType.FULL

    @pytest.mark.asyncio
    async def test_get_by_project(self, session):
        repo = IndexJobRepository(session)
        project_id = uuid4()
        for _ in range(3):
            job = IndexJob.create(project_id=project_id, type=IndexType.FULL)
            await repo.save(job)

        jobs = await repo.get_by_project(project_id)
        assert len(jobs) == 3

    @pytest.mark.asyncio
    async def test_get_latest_completed(self, session):
        repo = IndexJobRepository(session)
        project_id = uuid4()

        job = IndexJob.create(project_id=project_id, type=IndexType.FULL)
        job.start()
        job.complete(result={"files": 10}, state_hash="abc")
        await repo.save(job)

        latest = await repo.get_latest_completed(project_id)
        assert latest is not None
        assert latest.status.value == "completed"

    @pytest.mark.asyncio
    async def test_get_running(self, session):
        repo = IndexJobRepository(session)
        project_id = uuid4()

        job = IndexJob.create(project_id=project_id, type=IndexType.FULL)
        job.start()
        await repo.save(job)

        running = await repo.get_running(project_id)
        assert running is not None
        assert running.status.value == "running"

    @pytest.mark.asyncio
    async def test_update_job(self, session):
        repo = IndexJobRepository(session)
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        await repo.save(job)

        job.start()
        await repo.save(job)

        fetched = await repo.get_by_id(job.id)
        assert fetched.status.value == "running"


class TestFileIndexRepository:
    @pytest.mark.asyncio
    async def test_save_and_get(self, session):
        repo = FileIndexRepository(session)
        fi = FileIndex.create(
            project_id=uuid4(),
            file_path="src/main.py",
            content_hash="abc123",
            language="python",
        )
        await repo.save(fi)

        fetched = await repo.get_by_project_and_path(fi.project_id, "src/main.py")
        assert fetched is not None
        assert fetched.content_hash == "abc123"

    @pytest.mark.asyncio
    async def test_count_by_project(self, session):
        repo = FileIndexRepository(session)
        project_id = uuid4()
        for i in range(5):
            fi = FileIndex.create(
                project_id=project_id,
                file_path=f"src/file{i}.py",
                content_hash=f"hash{i}",
            )
            await repo.save(fi)

        count = await repo.count_by_project(project_id)
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_stale_files(self, session):
        repo = FileIndexRepository(session)
        project_id = uuid4()
        fi = FileIndex.create(
            project_id=project_id,
            file_path="src/main.py",
            content_hash="old_hash",
        )
        await repo.save(fi)

        stale = await repo.get_stale_files(
            project_id, {"src/main.py": "new_hash"}
        )
        assert len(stale) == 1
        assert stale[0].file_path == "src/main.py"


class TestExtractionCandidateRepository:
    @pytest.mark.asyncio
    async def test_save_and_get(self, session):
        job_repo = IndexJobRepository(session)
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        await job_repo.save(job)

        repo = ExtractionCandidateRepository(session)
        candidate = ExtractionCandidate.create(
            job_id=job.id,
            kind="decision",
            confidence=0.8,
            data={"title": "Use FastAPI"},
        )
        await repo.save(candidate)

        fetched = await repo.get_by_id(candidate.id)
        assert fetched is not None
        assert fetched.kind == "decision"

    @pytest.mark.asyncio
    async def test_dedup(self, session):
        job_repo = IndexJobRepository(session)
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        await job_repo.save(job)

        repo = ExtractionCandidateRepository(session)
        candidates = [
            ExtractionCandidate.create(
                job_id=job.id,
                kind="decision",
                confidence=0.8,
                dedup_key="same_key",
            ),
            ExtractionCandidate.create(
                job_id=job.id,
                kind="decision",
                confidence=0.8,
                dedup_key="same_key",
            ),
        ]
        await repo.save_many(candidates)

        # First one should be saved, second marked as duplicate
        existing = await repo.get_by_dedup_key("same_key")
        assert existing is not None

    @pytest.mark.asyncio
    async def test_count_by_project(self, session):
        project_id = uuid4()
        job_repo = IndexJobRepository(session)
        job = IndexJob.create(project_id=project_id, type=IndexType.FULL)
        await job_repo.save(job)

        repo = ExtractionCandidateRepository(session)
        for kind in ["decision", "decision", "bug"]:
            c = ExtractionCandidate.create(
                job_id=job.id,
                kind=kind,
                confidence=0.8,
            )
            await repo.save(c)

        counts = await repo.count_by_project(project_id)
        assert counts["decision"] == 2
        assert counts["bug"] == 1
