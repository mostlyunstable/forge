import pytest
from typer.testing import CliRunner
from forge.presentation.cli.plugins.automation import app

runner = CliRunner()

def test_index_cmd():
    result = runner.invoke(app, ["index"])
    assert result.exit_code == 0
    assert "Starting indexing process" in result.stdout
    assert "Indexing complete!" in result.stdout

def test_benchmark_cmd():
    result = runner.invoke(app, ["benchmark"])
    assert result.exit_code == 0
    assert "Starting Forge Benchmarks (Phases 1-3)" in result.stdout
    assert "Benchmarks completed!" in result.stdout

def test_doctor_cmd():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Running System Health Checks" in result.stdout
    assert "Vector Store" in result.stdout
    assert "Relational DB" in result.stdout
    assert "Index Staleness" in result.stdout

def test_config_cmd_list():
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "Current Configuration:" in result.stdout
    assert "environment" in result.stdout

def test_config_cmd_set():
    result = runner.invoke(app, ["config", "my_key", "my_value"])
    assert result.exit_code == 0
    assert "Configuration updated:" in result.stdout
    assert "my_key = my_value" in result.stdout

def test_completion_cmd():
    result = runner.invoke(app, ["completion"])
    assert result.exit_code == 0
    assert "Shell Completion Setup Instructions" in result.stdout
    assert "forge --install-completion bash" in result.stdout

def test_version_cmd():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Forge Phase 4" in result.stdout

def test_update_cmd():
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0
    assert "Checking for updates" in result.stdout
