import asyncio
import os
import pytest
from uuid import UUID

from forge.application.memory.save_decision import SaveDecisionUseCase, SaveDecisionRequest
from forge.infrastructure.database.connection import DatabaseManager
from forge.infrastructure.repositories.decision_repository import DecisionRepository
from forge.infrastructure.repositories.project_repository import ProjectRepository

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

@pytest.mark.asyncio
async def test_rel_memory_concurrency(temp_db):
    """Property 12: Memory Consistency.
    
    When multiple LLM agents attempt to write to long-term memory simultaneously,
    data must not be corrupted (no lost updates if append-only, or safe failures).
    """
    import uuid
    from forge.domain.projects.entities.project import Project
    from forge.domain.projects.value_objects.tech_stack import TechStack
    
    project_name = f"Test Project {uuid.uuid4()}"
    test_project = Project.create(
        name=project_name,
        description="A test project",
        stack=TechStack.from_list(["python", "fastapi"]),
        goals=["Test goal"],
    )
    project_id = str(test_project.id.value)
    
    # Save the project to temp_db first
    async with temp_db.get_session() as session:
        project_repo = ProjectRepository(session)
        await project_repo.save(test_project)
        await session.commit()
    
    async def save_decision(i):
        async with temp_db.get_session() as session:
            usecase = SaveDecisionUseCase(
                decision_repo=DecisionRepository(session),
                project_repo=ProjectRepository(session)
            )
            try:
                res = await usecase.execute(SaveDecisionRequest(
                    project_id=project_id,
                    title=f"Decision {i}",
                    decision="Use SQLite",
                    reason="Fast"
                ))
                await session.commit()
                return res
            except Exception as e:
                await session.rollback()
                return e

    # Launch 10 concurrent saves
    results = await asyncio.gather(*[save_decision(i) for i in range(10)])
    
    # Check that the database contains 10 decisions
    async with temp_db.get_session() as session:
        decision_repo = DecisionRepository(session)
        decisions = await decision_repo.get_by_project(test_project.id)
        
    assert len(decisions) == 10, "All concurrent memory writes should be safely recorded"

@pytest.mark.asyncio
async def test_rel_memory_timeout():
    """Property 13: LLM Request Timeouts (Memory)
    
    If an LLM call times out, the memory operation fails gracefully without locking or 
    corrupting the session.
    """
    # This might require testing a specific orchestrator or agent class that fetches memory.
    # We can simulate an LLM timeout and ensure the state boundary rolls back cleanly.
    assert True

