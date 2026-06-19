"""Repository integration tests using SQLite."""
import pytest
import pytest_asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from forge.infrastructure.database.base import Base
from forge.infrastructure.database.connection import DatabaseManager
from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.infrastructure.repositories.decision_repository import DecisionRepository
from forge.infrastructure.repositories.bug_repository import BugRepository
from forge.infrastructure.repositories.preference_repository import PreferenceRepository
from forge.domain.projects.entities.project import Project
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.value_objects.tech_stack import TechStack
from forge.domain.memory.entities.decision import ArchitectureDecision
from forge.domain.memory.entities.bug import Bug


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    
    await engine.dispose()


class TestProjectRepository:
    @pytest.mark.asyncio
    async def test_save_and_get(self, db_session):
        repo = ProjectRepository(db_session)
        project = Project.create(
            name="Repo Test",
            description="Test",
            stack=TechStack.from_list(["python"]),
        )
        saved = await repo.save(project)
        assert saved.id == project.id

        retrieved = await repo.get_by_id(project.id)
        assert retrieved is not None
        assert retrieved.name == "Repo Test"

    @pytest.mark.asyncio
    async def test_get_by_name(self, db_session):
        repo = ProjectRepository(db_session)
        project = Project.create(
            name="ByName Test",
            description="",
            stack=TechStack.from_list([]),
        )
        await repo.save(project)

        found = await repo.get_by_name("ByName Test")
        assert found is not None
        assert found.name == "ByName Test"

    @pytest.mark.asyncio
    async def test_get_all(self, db_session):
        repo = ProjectRepository(db_session)
        for i in range(3):
            await repo.save(Project.create(
                name=f"Project {i}",
                description="",
                stack=TechStack.from_list([]),
            ))
        
        projects = await repo.get_all()
        assert len(projects) == 3

    @pytest.mark.asyncio
    async def test_delete(self, db_session):
        repo = ProjectRepository(db_session)
        project = Project.create(
            name="Delete Test",
            description="",
            stack=TechStack.from_list([]),
        )
        await repo.save(project)
        
        deleted = await repo.delete(project.id)
        assert deleted is True
        
        retrieved = await repo.get_by_id(project.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_search_by_name(self, db_session):
        repo = ProjectRepository(db_session)
        await repo.save(Project.create(name="Alpha Project", description="", stack=TechStack.from_list([])))
        await repo.save(Project.create(name="Beta Project", description="", stack=TechStack.from_list([])))
        
        results = await repo.search_by_name("alpha")
        assert len(results) == 1
        assert results[0].name == "Alpha Project"


class TestDecisionRepository:
    @pytest.mark.asyncio
    async def test_save_and_get(self, db_session):
        project_repo = ProjectRepository(db_session)
        project = Project.create(name="Test", description="", stack=TechStack.from_list([]))
        await project_repo.save(project)

        repo = DecisionRepository(db_session)
        decision = ArchitectureDecision.create(
            project_id=project.id,
            title="Test Decision",
            decision="Do X",
            reason="Because",
        )
        saved = await repo.save(decision)
        
        retrieved = await repo.get_by_id(saved.id)
        assert retrieved is not None
        assert retrieved.title == "Test Decision"

    @pytest.mark.asyncio
    async def test_get_by_project(self, db_session):
        project_repo = ProjectRepository(db_session)
        project = Project.create(name="Test", description="", stack=TechStack.from_list([]))
        await project_repo.save(project)

        repo = DecisionRepository(db_session)
        await repo.save(ArchitectureDecision.create(
            project_id=project.id, title="D1", decision="X", reason="Y",
        ))
        await repo.save(ArchitectureDecision.create(
            project_id=project.id, title="D2", decision="A", reason="B",
        ))

        decisions = await repo.get_by_project(project.id)
        assert len(decisions) == 2


class TestBugRepository:
    @pytest.mark.asyncio
    async def test_save_and_get(self, db_session):
        project_repo = ProjectRepository(db_session)
        project = Project.create(name="Test", description="", stack=TechStack.from_list([]))
        await project_repo.save(project)

        repo = BugRepository(db_session)
        bug = Bug.create(
            project_id=project.id,
            title="Test Bug",
            problem="Crash",
            root_cause="Null",
            solution="Check",
        )
        saved = await repo.save(bug)
        
        retrieved = await repo.get_by_id(saved.id)
        assert retrieved is not None
        assert retrieved.title == "Test Bug"

    @pytest.mark.asyncio
    async def test_get_by_project(self, db_session):
        project_repo = ProjectRepository(db_session)
        project = Project.create(name="Test", description="", stack=TechStack.from_list([]))
        await project_repo.save(project)

        repo = BugRepository(db_session)
        await repo.save(Bug.create(
            project_id=project.id, title="B1", problem="P", root_cause="R", solution="S",
        ))

        bugs = await repo.get_by_project(project.id)
        assert len(bugs) == 1
