"""API integration tests using TestClient."""
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
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

    from forge.infrastructure.database.connection import DatabaseManager
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


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.mark.asyncio
async def test_health_endpoint(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_metrics_endpoint(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_unauthorized_access(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/projects")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_project(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "API Test Project", "description": "Test"},
            headers=auth_headers,
        )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "API Test Project"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_create_and_get_project(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/v1/projects",
            json={"name": "Get Test", "description": "Test"},
            headers=auth_headers,
        )
        project_id = create_resp.json()["id"]

        get_resp = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Get Test"


@pytest.mark.asyncio
async def test_update_project(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/v1/projects",
            json={"name": "Update Test", "description": "Original"},
            headers=auth_headers,
        )
        project_id = create_resp.json()["id"]

        update_resp = await client.put(
            f"/api/v1/projects/{project_id}",
            json={"description": "Updated"},
            headers=auth_headers,
        )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Updated"


@pytest.mark.asyncio
async def test_delete_project(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/v1/projects",
            json={"name": "Delete Test"},
            headers=auth_headers,
        )
        project_id = create_resp.json()["id"]

        delete_resp = await client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True


@pytest.mark.asyncio
async def test_create_decision(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        proj_resp = await client.post(
            "/api/v1/projects",
            json={"name": "Decision Test"},
            headers=auth_headers,
        )
        project_id = proj_resp.json()["id"]

        response = await client.post(
            "/api/v1/memory/decisions",
            json={
                "project_id": project_id,
                "title": "Use Type hints",
                "decision": "Use type hints everywhere",
                "reason": "Better code quality",
            },
            headers=auth_headers,
        )
    assert response.status_code == 201
    assert response.json()["title"] == "Use Type hints"


@pytest.mark.asyncio
async def test_create_bug(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        proj_resp = await client.post(
            "/api/v1/projects",
            json={"name": "Bug Test"},
            headers=auth_headers,
        )
        project_id = proj_resp.json()["id"]

        response = await client.post(
            "/api/v1/memory/bugs",
            json={
                "project_id": project_id,
                "title": "Test bug",
                "problem": "Something breaks",
                "root_cause": "Missing check",
                "solution": "Add check",
                "severity": "high",
            },
            headers=auth_headers,
        )
    assert response.status_code == 201
    assert response.json()["title"] == "Test bug"
    assert response.json()["severity"] == "high"


@pytest.mark.asyncio
async def test_invalid_severity(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        proj_resp = await client.post(
            "/api/v1/projects",
            json={"name": "Validation Test"},
            headers=auth_headers,
        )
        project_id = proj_resp.json()["id"]

        response = await client.post(
            "/api/v1/memory/bugs",
            json={
                "project_id": project_id,
                "title": "Test",
                "problem": "Test",
                "severity": "invalid",
            },
            headers=auth_headers,
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_uuid(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/memory/decisions",
            json={
                "project_id": "not-a-uuid",
                "title": "Test",
                "decision": "Test",
                "reason": "Test",
            },
            headers=auth_headers,
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_project_not_found(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
    assert response.status_code == 404
    assert response.json()["error_code"] == "PROJECT_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_preference(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/memory/preferences",
            json={"key": "editor", "value": "vim", "confidence": 0.9},
            headers=auth_headers,
        )
    assert response.status_code == 201
    assert response.json()["key"] == "editor"


@pytest.mark.asyncio
async def test_list_preferences(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/memory/preferences",
            json={"key": "test", "value": "val"},
            headers=auth_headers,
        )
        response = await client.get("/api/v1/memory/preferences", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] >= 1
