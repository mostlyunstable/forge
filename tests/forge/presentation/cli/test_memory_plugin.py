import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from forge.domain.memory.repository_contracts.memory_repository import IMemoryRepository
from forge.presentation.cli.di import cli_container
from forge.presentation.cli.plugins.memory import app as memory_app
from typer.testing import CliRunner

runner = CliRunner()

@pytest.fixture
def mock_memory_repo():
    repo = AsyncMock(spec=IMemoryRepository)
    
    # Mocking some memories
    mem1 = MagicMock()
    mem1.id.value = uuid.uuid4()
    mem1.title = "Test ADR"
    mem1.memory_type = "decision"
    mem1.status = "Accepted"
    mem1.created_at = datetime.now(timezone.utc)
    
    mem2 = MagicMock()
    mem2.id.value = uuid.uuid4()
    mem2.title = "Test Bug"
    mem2.memory_type = "bug"
    mem2.severity = "High"
    mem2.resolved = False
    mem2.created_at = datetime.now(timezone.utc)
    
    repo.get_by_project.return_value = [mem1, mem2]
    
    cli_container.register_instance(IMemoryRepository, repo)
    return repo

def test_list_memories_table(mock_memory_repo):
    result = runner.invoke(memory_app, ["list"])
    assert result.exit_code == 0
    assert "Test ADR" in result.stdout
    assert "Test Bug" in result.stdout

def test_list_memories_json(mock_memory_repo):
    result = runner.invoke(memory_app, ["list", "--json"])
    assert result.exit_code == 0
    assert '"title": "Test ADR"' in result.stdout
    assert '"type": "decision"' in result.stdout

def test_list_adrs(mock_memory_repo):
    result = runner.invoke(memory_app, ["adr"])
    assert result.exit_code == 0
    assert "Test ADR" in result.stdout
    assert "Test Bug" not in result.stdout

def test_list_bugs_yaml(mock_memory_repo):
    result = runner.invoke(memory_app, ["bug", "--yaml"])
    assert result.exit_code == 0
    assert "title: Test Bug" in result.stdout
    assert "severity: High" in result.stdout
    assert "Test ADR" not in result.stdout
