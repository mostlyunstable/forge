import pytest
import os
from typer.testing import CliRunner
import uuid
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from forge.presentation.cli.plugins.session import app as session_app
from forge.presentation.cli.di import cli_container
from forge.domain.conversation.repository_contracts.conversation_repository import IConversationRepository
from forge.domain.conversation.value_objects.conversation_state import ConversationState

runner = CliRunner()

@pytest.fixture
def mock_session_repo():
    repo = AsyncMock(spec=IConversationRepository)
    
    conv1 = MagicMock()
    conv1.id.value = uuid.uuid4()
    conv1.title = "Test Session 1"
    try:
        conv1.state.value = "ACTIVE"
    except Exception:
        conv1.state = "ACTIVE"
    conv1.messages = []
    conv1.created_at = datetime.now()
    
    repo.get_by_project.return_value = [conv1]
    repo.get_by_id.return_value = conv1
    repo.delete.return_value = True
    
    cli_container.register_instance(IConversationRepository, repo)
    return repo, conv1

def test_list_sessions(mock_session_repo):
    repo, conv1 = mock_session_repo
    result = runner.invoke(session_app, ["list"])
    assert result.exit_code == 0
    assert "Test Session 1" in result.stdout

def test_new_session(mock_session_repo):
    repo, _ = mock_session_repo
    result = runner.invoke(session_app, ["new", "--title", "My New Session"])
    assert result.exit_code == 0
    assert "Created new session" in result.stdout
    repo.save.assert_called_once()

def test_rename_session(mock_session_repo):
    repo, conv1 = mock_session_repo
    session_id = str(conv1.id.value)
    result = runner.invoke(session_app, ["rename", session_id, "Renamed Session"])
    assert result.exit_code == 0
    assert "Renamed session to: Renamed Session" in result.stdout
    repo.save.assert_called_once()

def test_archive_session(mock_session_repo):
    repo, conv1 = mock_session_repo
    session_id = str(conv1.id.value)
    result = runner.invoke(session_app, ["archive", session_id])
    assert result.exit_code == 0
    assert "Archived session" in result.stdout
    repo.save.assert_called_once()

def test_delete_session(mock_session_repo):
    repo, conv1 = mock_session_repo
    session_id = str(conv1.id.value)
    result = runner.invoke(session_app, ["delete", session_id])
    assert result.exit_code == 0
    assert "Deleted session" in result.stdout
    repo.delete.assert_called_once()

def test_export_session(mock_session_repo):
    repo, conv1 = mock_session_repo
    session_id = str(conv1.id.value)
    
    # Mocking a message
    msg = MagicMock()
    msg.role = "user"
    msg.content = "Hello there"
    conv1.messages = [msg]
    
    out_file = f"test_export_{session_id}.md"
    result = runner.invoke(session_app, ["export", session_id, "--out", out_file])
    assert result.exit_code == 0
    assert "Exported session to" in result.stdout
    
    assert os.path.exists(out_file)
    with open(out_file, "r") as f:
        content = f.read()
    assert "# Test Session 1" in content
    assert "### USER" in content
    assert "Hello there" in content
    
    os.remove(out_file)
