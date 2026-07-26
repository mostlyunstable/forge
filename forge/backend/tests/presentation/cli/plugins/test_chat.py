import pytest
import typer
from unittest.mock import patch, AsyncMock, MagicMock
from forge.presentation.cli.plugins.chat import register

@pytest.fixture
def mock_app():
    return typer.Typer()

def test_register_command(mock_app):
    register(mock_app)
    # Ensure command was registered
    commands = [cmd.name for cmd in mock_app.registered_commands]
    assert "chat" in commands

@pytest.mark.asyncio
@patch("forge.presentation.cli.plugins.chat.PromptSession")
@patch("forge.presentation.cli.plugins.chat.console.print")
@patch("forge.presentation.cli.plugins.chat.database_manager")
@patch("forge.presentation.cli.plugins.chat.ConversationRepository")
@patch("forge.presentation.cli.plugins.chat.ProjectRepository")
@patch("forge.presentation.cli.plugins.chat.ConversationContextManager")
@patch("forge.presentation.cli.plugins.chat.ReasoningEngine")
async def test_run_chat(
    mock_engine, mock_context_manager, mock_project_repo,
    mock_conv_repo, mock_db_manager, mock_console_print, mock_prompt_session
):
    from forge.presentation.cli.plugins.chat import run_chat
    
    # Setup mocks
    mock_session = AsyncMock()
    mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session
    
    # Mock project repo
    mock_project_repo_instance = AsyncMock()
    mock_project_repo.return_value = mock_project_repo_instance
    mock_project_repo_instance.list_all.return_value = []
    
    # Mock conversation repo
    mock_conv_repo_instance = AsyncMock()
    mock_conv_repo.return_value = mock_conv_repo_instance
    mock_conv_repo_instance.get_by_id.return_value = MagicMock(messages=[])
    
    # Mock context manager
    mock_context_manager_instance = AsyncMock()
    mock_context_manager.return_value = mock_context_manager_instance
    mock_context_manager_instance.build_context.return_value = {
        "summary": "Mock summary",
        "messages": [],
        "retrieved": [],
        "total_tokens_estimated": 10
    }
    
    # Mock reasoning engine
    mock_engine_instance = AsyncMock()
    mock_engine.return_value = mock_engine_instance
    
    async def mock_stream(*args, **kwargs):
        yield "Hello"
        yield " World"
        
    mock_engine_instance.generate_response_stream = mock_stream
    
    # Mock prompt session
    mock_session_instance = AsyncMock()
    mock_prompt_session.return_value = mock_session_instance
    
    # Simulate user typing "hello" then "/exit"
    mock_session_instance.prompt_async.side_effect = ["hello", "/exit"]
    
    await run_chat()
    
    assert mock_session_instance.prompt_async.call_count == 2
    # It should have printed Goodbye!
    mock_console_print.assert_any_call("[bold green]Goodbye![/bold green]")
