import pytest
import asyncio
import uuid
import os
from datetime import UTC, datetime
from sqlalchemy import select

from forge.infrastructure.database.connection import DatabaseManager
from forge.domain.indexing.entities.index_job import IndexJob
from forge.domain.indexing.value_objects.index_type import IndexType
from forge.domain.indexing.value_objects.job_status import JobStatus
from forge.infrastructure.database.models.index_job_model import IndexJobModel

import tempfile

@pytest.fixture
async def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{f.name}"
        manager = DatabaseManager()
        await manager.run_migrations()
        yield manager
        await manager.close()
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]

from forge.domain.indexing.entities.index_job import IndexJob
from forge.domain.indexing.value_objects.index_type import IndexType
from forge.domain.indexing.value_objects.job_status import JobStatus
from forge.infrastructure.database.models.index_job_model import IndexJobModel

@pytest.mark.asyncio
async def test_rel_crash_recovery(temp_db):
    """Property 3, 22: Crash and Startup Recovery.
    
    If the application crashes while a job is running, the job is left in a RUNNING
    state in the database. On next startup, the system should detect orphaned jobs
    and mark them as FAILED or resume them.
    """
    
    project_id = uuid.uuid4()
    job_id = uuid.uuid4()
    
    # 1. Simulate an interrupted job directly in the DB
    async with temp_db.get_session() as session:
        job = IndexJobModel(
            id=job_id.hex,
            project_id=project_id.hex,
            type=IndexType.FULL.value,
            status=JobStatus.RUNNING.value,
            created_by="test",
            created_at=datetime.now(UTC),
            started_at=datetime.now(UTC)
        )
        session.add(job)
        await session.commit()
        
    # 2. Simulate application startup
    # Patch global database_manager to use our temp_db engine and session factory
    from forge.infrastructure.database.connection import database_manager
    orig_engine = database_manager._engine
    orig_factory = database_manager._session_factory
    
    database_manager._engine = temp_db._engine
    database_manager._session_factory = temp_db._session_factory
    
    try:
        # We call the FastAPI lifespan to simulate a full boot up
        from forge.presentation.app import lifespan, create_app
        app = create_app()
        
        async with lifespan(app):
            # The application is running. The background recovery should have run.
            # Allow a tiny bit of time for background tasks if any
            await asyncio.sleep(0.1)
    finally:
        database_manager._engine = orig_engine
        database_manager._session_factory = orig_factory
        
    # 3. Assert the job is no longer RUNNING
    async with temp_db.get_session() as session:
        result = await session.execute(
            select(IndexJobModel).filter_by(id=job_id.hex)
        )
        persisted_job = result.scalar_one_or_none()
        
        assert persisted_job is not None
        assert persisted_job.status != JobStatus.RUNNING.value, (
            "Startup recovery failed: Job was left in a RUNNING state after a crash."
        )
