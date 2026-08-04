"""API tests for analysis endpoints."""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from forge.infrastructure.database.base import Base
from forge.infrastructure.database.connection import database_manager
from forge.presentation.app import create_app
from forge.presentation.middleware.auth import create_access_token


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-32-bytes"
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


@pytest.mark.asyncio
async def test_analyze_pr_requires_project(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/analysis/pr",
            json={"project_id": "nonexistent-id"},
            headers=auth_headers,
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_analyze_pr_requires_auth(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/analysis/pr",
            json={"project_id": "test-id"},
        )
        assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_reports_requires_project_id(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analysis/reports", headers=auth_headers)
        assert resp.status_code == 422  # Missing required query param


@pytest.mark.asyncio
async def test_get_report_not_found(app, auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/analysis/reports/nonexistent-id",
            headers=auth_headers,
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_full_analysis_flow(app, auth_headers):
    """Integration test: create project -> analyze -> get report."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a project first
        resp = await client.post(
            "/api/v1/projects",
            json={"name": "Test Project", "description": "Test"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        project_id = resp.json()["id"]

        # Analyze a PR (with empty diff — stub provider)
        resp = await client.post(
            "/api/v1/analysis/pr",
            json={"project_id": project_id, "pr_number": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["project_id"] == project_id
        assert data["pr_number"] == 1
        assert "risk_score" in data
        assert "risk_level" in data
        report_id = data["report_id"]

        # Get the report
        resp = await client.get(
            f"/api/v1/analysis/reports/{report_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == report_id

        # List reports
        resp = await client.get(
            f"/api/v1/analysis/reports?project_id={project_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
