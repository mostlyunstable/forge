import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch

from forge.presentation.api.routers.conversation import router
from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.value_objects.conversation_id import ConversationId

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
    with patch("forge.application.conversation.create_conversation.CreateConversationUseCase") as MockUseCase:
        use_case = MockUseCase.return_value
        mock_result = AsyncMock()
        mock_result.id = "conv-123"
        mock_result.project_id = "proj-123"
        mock_result.title = "Test Title"
        use_case.execute = AsyncMock(return_value=mock_result)

        response = client.post("/api/conversations/start", json={
            "project_id": "proj-123",
            "title": "Test Title"
        })

        assert response.status_code == 201
        assert response.json() == {
            "conversation_id": "conv-123",
            "project_id": "proj-123",
            "title": "Test Title"
        }

@pytest.mark.asyncio
async def test_start_session_project_not_found(mock_project_repo):
    mock_project_repo.get_by_id = AsyncMock(return_value=None)
    response = client.post("/api/conversations/start", json={
        "project_id": "nonexistent",
        "title": "New"
    })
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_send_message_success(mock_conversation_repo):
    conv_id_str = "00000000-0000-0000-0000-000000000000"
    mock_conv = Conversation.create("proj-1", "Test")
    mock_conv.id = ConversationId.from_string(conv_id_str)
    mock_conversation_repo.get_by_id.return_value = mock_conv

    with patch("forge.presentation.api.routers.conversation.ContextRetriever") as MockRetriever, \
         patch("forge.presentation.api.routers.conversation.ConversationContextManager") as MockContextMgr, \
         patch("forge.presentation.api.routers.conversation.ReasoningEngine") as MockReasoningEngine, \
         patch("forge.presentation.api.routers.conversation.QdrantClient") as MockQdrant:
        
        mock_retriever = MockRetriever.return_value
        mock_retriever.retrieve = AsyncMock(return_value={
            "relevant_code": [{"payload": {"content": "code snippet", "file_path": "main.py"}, "score": 0.9}]
        })

        mock_context_mgr = MockContextMgr.return_value
        mock_context_mgr.build_context = AsyncMock(return_value={
            "summary": "a summary",
            "messages": [{"role": "user", "content": "Hello"}],
            "retrieved": [{"source": "main.py", "content": "code snippet", "score": 0.9}],
            "total_tokens_estimated": 10
        })

        mock_reasoning_engine = MockReasoningEngine.return_value
        mock_reasoning_engine.generate_response = AsyncMock(return_value="AI Reply")

        response = client.post(f"/api/conversations/{conv_id_str}/messages", json={
            "message": "How does it work?"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conv_id_str
        assert data["response"] == "AI Reply"
        assert len(data["citations"]) == 1
        assert data["citations"][0]["source"] == "main.py"

@pytest.mark.asyncio
async def test_send_message_conversation_not_found(mock_conversation_repo):
    conv_id_str = "00000000-0000-0000-0000-000000000000"
    mock_conversation_repo.get_by_id.return_value = None
    
    response = client.post(f"/api/conversations/{conv_id_str}/messages", json={
        "message": "Hello"
    })
    
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_send_message_invalid_id_format():
    response = client.post("/api/conversations/invalid-id/messages", json={
        "message": "Hello"
    })
    assert response.status_code == 400
