"""API tests for indexing routes."""
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from forge.infrastructure.database.base import Base
from forge.presentation.app import create_app
from forge.presentation.middleware.auth import create_access_token
from forge.infrastructure.database.connection import database_manager


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    database_manager._engine = engine
    database_manager._session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    yield
    await engine.dispose()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def auth_token():
    return create_access_token({"sub": "test-user"})


@pytest.mark.asyncio
async def test_get_index_status(app, auth_token):
    """Test GET /api/v1/index/status/{project_id}"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = str(uuid4())
        response = await client.get(
            f"/api/v1/index/status/{project_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert data["total_files_indexed"] == 0


@pytest.mark.asyncio
async def test_list_index_jobs(app, auth_token):
    """Test GET /api/v1/index/jobs"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = str(uuid4())
        response = await client.get(
            f"/api/v1/index/jobs?project_id={project_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["jobs"] == []
        assert data["project_id"] == project_id


@pytest.mark.asyncio
async def test_get_index_job_not_found(app, auth_token):
    """Test GET /api/v1/index/jobs/{job_id} with invalid ID"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/index/jobs/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_start_index_invalid_project(app, auth_token):
    """Test POST /api/v1/index/jobs with invalid project"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/index/jobs",
            json={
                "project_id": "invalid-id",
                "repo_path": "/tmp/test",
                "type": "full",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_start_index_nonexistent_project(app, auth_token):
    """Test POST /api/v1/index/jobs with nonexistent project"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/index/jobs",
            json={
                "project_id": str(uuid4()),
                "repo_path": "/tmp/test",
                "type": "full",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_start_index_unsupported_type(app, auth_token):
    """Test POST /api/v1/index/jobs with unsupported type"""
    # First create a project
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "name": "test-project-index",
                "description": "Test project",
                "stack": ["python"],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        response = await client.post(
            "/api/v1/index/jobs",
            json={
                "project_id": project_id,
                "repo_path": "/tmp/test",
                "type": "unsupported",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 400
