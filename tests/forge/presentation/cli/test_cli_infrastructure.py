import pytest
import typer
from typer.testing import CliRunner
import sys

from forge.presentation.cli.app import app, setup_global_exception_handler
from forge.presentation.cli.di import cli_container
from forge.presentation.cli.plugin_loader import load_plugins

runner = CliRunner()

def test_di_container_registration_and_resolution():
    class DummyInterface:
        pass
        
    class DummyImpl(DummyInterface):
        pass
        
    cli_container.register(DummyInterface, lambda: DummyImpl())
    
    instance1 = cli_container.resolve(DummyInterface)
    instance2 = cli_container.resolve(DummyInterface)
    
    assert isinstance(instance1, DummyImpl)
    assert instance1 is instance2 # Should be singleton by default in our basic implementation

def test_di_container_unregistered():
    class UnregisteredInterface:
        pass
        
    with pytest.raises(ValueError, match="No provider registered"):
        cli_container.resolve(UnregisteredInterface)

def test_plugin_loader(tmp_path, monkeypatch):
    # Create a dummy plugin
    plugins_dir = tmp_path / "dummy_plugins"
    plugins_dir.mkdir()
    (plugins_dir / "__init__.py").touch()
    
    plugin_code = """
import typer
def register(app: typer.Typer):
    @app.command()
    def dummy_command():
        typer.echo("Dummy command executed")
"""
    (plugins_dir / "plugin_a.py").write_text(plugin_code)
    
    # We need to add tmp_path to sys.path to import it
    monkeypatch.syspath_prepend(str(tmp_path))
    
    test_app = typer.Typer()
    @test_app.callback()
    def callback():
        pass
        
    loaded = load_plugins(test_app, "dummy_plugins")
    
    assert "dummy_plugins.plugin_a" in loaded
    
    # Run the dummy command
    result = runner.invoke(test_app, ["dummy-command"])
    assert result.exit_code == 0
    assert "Dummy command executed" in result.stdout

def test_global_exception_handler(capsys):
    setup_global_exception_handler()
    
    # Simulate an exception
    try:
        raise ValueError("This is a test error")
    except ValueError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sys.excepthook(exc_type, exc_value, exc_traceback)
        
    captured = capsys.readouterr()
    assert "An unexpected error occurred: This is a test error" in captured.err
    assert "Please check the system logs for more details" in captured.err
