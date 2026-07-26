"""API tests for conversation endpoints."""
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


async def _create_project(client: AsyncClient, headers: dict) -> str:
    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Test Project",
            "description": "A test project",
            "stack": ["python"],
        },
        headers=headers,
    )
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_conversation(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await _create_project(client, auth_headers)

        response = await client.post(
            "/api/v1/conversations",
            json={"project_id": project_id, "title": "Debug session"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Debug session"
        assert data["project_id"] == project_id
        assert "id" in data


@pytest.mark.asyncio
async def test_list_conversations(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await _create_project(client, auth_headers)

        # Create 3 conversations
        for i in range(3):
            await client.post(
                "/api/v1/conversations",
                json={"project_id": project_id, "title": f"Conv {i}"},
                headers=auth_headers,
            )

        response = await client.get(
            f"/api/v1/conversations?project_id={project_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["conversations"]) == 3


@pytest.mark.asyncio
async def test_get_conversation_history(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await _create_project(client, auth_headers)

        create_resp = await client.post(
            "/api/v1/conversations",
            json={"project_id": project_id, "title": "Test"},
            headers=auth_headers,
        )
        conv_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/conversations/{conv_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test"
        assert data["messages"] == []


@pytest.mark.asyncio
async def test_rename_conversation(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await _create_project(client, auth_headers)

        create_resp = await client.post(
            "/api/v1/conversations",
            json={"project_id": project_id, "title": "Old Title"},
            headers=auth_headers,
        )
        conv_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/conversations/{conv_id}",
            json={"title": "New Title"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_delete_conversation(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await _create_project(client, auth_headers)

        create_resp = await client.post(
            "/api/v1/conversations",
            json={"project_id": project_id, "title": "To Delete"},
            headers=auth_headers,
        )
        conv_id = create_resp.json()["id"]

        response = await client.delete(
            f"/api/v1/conversations/{conv_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify 404
        get_resp = await client.get(
            f"/api/v1/conversations/{conv_id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_send_message(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await _create_project(client, auth_headers)

        create_resp = await client.post(
            "/api/v1/conversations",
            json={"project_id": project_id, "title": "Chat"},
            headers=auth_headers,
        )
        conv_id = create_resp.json()["id"]

        response = await client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"message": "Hello Forge"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["response"] is not None
        assert data["conversation_id"] == conv_id


@pytest.mark.asyncio
async def test_search_conversations(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await _create_project(client, auth_headers)

        await client.post(
            "/api/v1/conversations",
            json={"project_id": project_id, "title": "Auth debugging session"},
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/conversations",
            json={"project_id": project_id, "title": "DB optimization"},
            headers=auth_headers,
        )

        response = await client.get(
            f"/api/v1/conversations/search?project_id={project_id}&q=auth",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "auth" in data["conversations"][0]["title"].lower()


@pytest.mark.asyncio
async def test_conversation_not_found(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/conversations/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert response.json()["error_code"] == "CONVERSATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_conversation_unauthorized(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/conversations?project_id=00000000-0000-0000-0000-000000000000",
        )
        assert response.status_code == 401
