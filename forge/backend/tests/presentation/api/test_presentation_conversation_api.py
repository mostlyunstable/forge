from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.presentation.api.routers.conversation import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def mock_project_repo():
    with patch("forge.presentation.api.routers.conversation.ProjectRepository") as MockRepo:
        repo = MockRepo.return_value
        repo.get_by_id = AsyncMock(return_value=True)
        yield repo


@pytest.fixture
def mock_conversation_repo():
    with patch("forge.presentation.api.routers.conversation.ConversationRepository") as MockRepo:
        repo = MockRepo.return_value
        repo.get_by_id = AsyncMock()
        repo.save = AsyncMock()
        yield repo


@pytest.mark.asyncio
async def test_start_session_success(mock_project_repo, mock_conversation_repo):
    with patch(
        "forge.application.conversation.create_conversation.CreateConversationUseCase"
    ) as MockUseCase:
        use_case = MockUseCase.return_value
        mock_result = AsyncMock()
        mock_result.id = "conv-123"
        mock_result.project_id = "12345678-1234-5678-1234-567812345678"
        mock_result.title = "Test Title"
        use_case.execute = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/conversations/start", json={"project_id": "12345678-1234-5678-1234-567812345678", "title": "Test Title"}
        )

        assert response.status_code == 201
        assert response.json() == {
            "conversation_id": "conv-123",
            "project_id": "12345678-1234-5678-1234-567812345678",
            "title": "Test Title",
        }


@pytest.mark.asyncio
async def test_start_session_project_not_found(mock_project_repo):
    mock_project_repo.get_by_id = AsyncMock(return_value=None)
    response = client.post(
        "/api/conversations/start", json={"project_id": "12345678-1234-5678-1234-567812345678", "title": "New"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_send_message_success(mock_conversation_repo):
    conv_id_str = "00000000-0000-0000-0000-000000000000"
    mock_conv = Conversation.create("proj-1", "Test")
    mock_conv.id = ConversationId.from_string(conv_id_str)
    mock_conversation_repo.get_by_id.return_value = mock_conv

    from forge.presentation.api.routers.conversation import get_send_message_use_case
    mock_use_case = AsyncMock()
    
    async def mock_execute(*args, **kwargs):
        yield {"type": "text", "content": "AI Reply"}
        yield {"type": "citation", "source": "main.py"}
    
    mock_use_case.execute = mock_execute
    app.dependency_overrides[get_send_message_use_case] = lambda: mock_use_case
    
    response = client.post(
        f"/api/conversations/{conv_id_str}/messages", json={"message": "How does it work?"}
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "data: {\"type\": \"text\", \"content\": \"AI Reply\"}" in content
    assert "data: {\"type\": \"citation\", \"source\": \"main.py\"}" in content
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_send_message_conversation_not_found(mock_conversation_repo):
    conv_id_str = "00000000-0000-0000-0000-000000000000"
    mock_conversation_repo.get_by_id.return_value = None

    response = client.post(f"/api/conversations/{conv_id_str}/messages", json={"message": "Hello"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_send_message_invalid_id_format():
    response = client.post("/api/conversations/invalid-id/messages", json={"message": "Hello"})
    assert response.status_code == 400
