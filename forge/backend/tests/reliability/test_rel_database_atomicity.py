import pytest
import asyncio
import uuid
from datetime import datetime
from unittest.mock import patch
from sqlalchemy import select
from forge.infrastructure.database.connection import DatabaseManager
from forge.infrastructure.database.models.project_model import ProjectModel
from forge.infrastructure.database.models.memory_model import DecisionModel

import os

@pytest.fixture
async def temp_db():
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    manager = DatabaseManager()
    await manager.run_migrations()
    yield manager
    await manager.close()
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]

@pytest.mark.asyncio
async def test_rel_db_multistep_commit_failure(temp_db):
    """Test Property 1: What happens if session.commit() crashes during a multi-step operation?"""
    
    proj_id = uuid.uuid4().hex
    dec_id = uuid.uuid4().hex
    original_commit = "sqlalchemy.ext.asyncio.AsyncSession.commit"
    
    with patch(original_commit, side_effect=RuntimeError("Simulated Commit Crash")):
        try:
            async with temp_db.get_session() as session:
                new_project = ProjectModel(id=proj_id, name=proj_id, description="Testing", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
                session.add(new_project)
                
                # Assume this flush is successful and we continue to insert a child object
                await session.flush()
                
                new_decision = DecisionModel(id=dec_id, project_id=proj_id, title="Test Dec", decision="Test Decision", reason="Test Reason", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
                session.add(new_decision)
                
                # When exiting the block, get_session() calls await session.commit(), which we mocked to crash.
        except RuntimeError:
            pass

    # Verify state rolled back completely
    async with temp_db.get_session() as session:
        proj_result = await session.execute(select(ProjectModel).filter_by(id=proj_id))
        dec_result = await session.execute(select(DecisionModel).filter_by(id=dec_id))
        
        assert proj_result.scalar_one_or_none() is None, "Database atomicity violated: Partial Project persisted despite commit failure."
        assert dec_result.scalar_one_or_none() is None, "Database atomicity violated: Partial Decision persisted despite commit failure."

@pytest.mark.asyncio
async def test_rel_db_failure_between_inserts(temp_db):
    """Test Property 1: What happens if an exception is raised between operations, before commit?"""
    
    proj_id = uuid.uuid4().hex
    dec_id = uuid.uuid4().hex
    try:
        async with temp_db.get_session() as session:
            new_project = ProjectModel(id=proj_id, name=proj_id, description="Testing", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            session.add(new_project)
            await session.flush() # Insert hits the DB
            
            # Simulate application failure here (e.g. OOM, ValueError, validation error)
            raise ValueError("Application logic crashed after first insert")
            
            # This is never reached
            new_decision = DecisionModel(id=dec_id, project_id=proj_id, title="Test Dec", decision="Test Decision", reason="Test Reason", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            session.add(new_decision)
    except ValueError:
        pass

    # Verify state rolled back completely
    async with temp_db.get_session() as session:
        proj_result = await session.execute(select(ProjectModel).filter_by(id=proj_id))
        assert proj_result.scalar_one_or_none() is None, "Database atomicity violated: Application crash left uncommitted data in DB."

@pytest.mark.asyncio
async def test_rel_db_crash_after_commit(temp_db):
    """Test Property 1: What happens if we crash exactly after the DB commits, but before the caller resumes?"""
    
    # If it's already committed, we EXPECT the data to be there. But the caller might think it failed.
    # We verify the data is there.
    proj_id = uuid.uuid4().hex
    try:
        async with temp_db.get_session() as session:
            new_project = ProjectModel(id=proj_id, name=proj_id, description="Testing", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            session.add(new_project)
            # The commit succeeds implicitly at exit
        
        # Immediate application crash
        raise MemoryError("Killed right after commit")
    except MemoryError:
        pass

    # Verify data is PRESENT
    async with temp_db.get_session() as session:
        proj_result = await session.execute(select(ProjectModel).filter_by(id=proj_id))
        assert proj_result.scalar_one_or_none() is not None, "Data lost even though commit succeeded!"

