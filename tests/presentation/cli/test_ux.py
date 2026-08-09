import pytest
from forge.presentation.cli.dashboard import Dashboard
from forge.presentation.cli.main import IntentRouter, app
from forge.presentation.cli.renderer import OutputRenderer
from typer.testing import CliRunner

runner = CliRunner()

def test_intent_router():
    assert IntentRouter.route("Why was X built?") == "Explain"
    assert IntentRouter.route("Find user service") == "Search"
    assert IntentRouter.route("Show memory state") == "Memory Traversal"
    assert IntentRouter.route("Do something else") == "Unknown Intent"

def test_natural_language_mode():
    result = runner.invoke(app, ["Why", "was", "X", "built?"])
    assert result.exit_code == 0
    assert "Routed 'Why was X built?' to:" in result.stdout
    assert "Explain" in result.stdout

def test_renderer_instantiation():
    renderer = OutputRenderer()
    assert renderer is not None

@pytest.mark.asyncio
async def test_dashboard_startup():
    info = {
        "repo": "test_repo",
        "branch": "main",
        "index_status": "Ready",
        "memory_count": 10,
        "active_sessions": 2
    }
    app = Dashboard(info)
    async with app.run_test() as pilot:
        # Check initial state
        assert app.project_info["repo"] == "test_repo"
        # Test f1 action
        await pilot.press("f1")
        await pilot.pause()
        assert "Opened Chat view." in str(app.query_one("#main-text").render())
        # Test f2 action
        await pilot.press("f2")
        await pilot.pause()
        assert "Opened Search view." in str(app.query_one("#main-text").render())
