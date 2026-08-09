from unittest.mock import MagicMock

import pytest
from forge.application.discovery import (
    ContextRetriever,
    ExplainResult,
    GraphResult,
    IGraphAdapter,
    ReasoningEngine,
    SearchResult,
)
from forge.presentation.cli.di import cli_container
from forge.presentation.cli.plugins.discovery import app
from typer.testing import CliRunner

runner = CliRunner()

@pytest.fixture
def mock_retriever():
    mock = MagicMock(spec=ContextRetriever)
    cli_container.register_instance(ContextRetriever, mock)
    return mock

@pytest.fixture
def mock_engine():
    mock = MagicMock(spec=ReasoningEngine)
    cli_container.register_instance(ReasoningEngine, mock)
    return mock

@pytest.fixture
def mock_graph():
    mock = MagicMock(spec=IGraphAdapter)
    cli_container.register_instance(IGraphAdapter, mock)
    return mock

def test_search_command(mock_retriever):
    mock_retriever.search.return_value = SearchResult(
        content="Found 42 results for 'test'",
        citations=["file1.py:10", "file2.py:20"]
    )
    
    result = runner.invoke(app, ["search", "test"])
    
    assert result.exit_code == 0
    assert "Search: test" in result.stdout
    assert "Found 42 results" in result.stdout
    assert "file1.py:10" in result.stdout
    mock_retriever.search.assert_called_once_with("test")

def test_explain_command(mock_engine):
    mock_engine.explain.return_value = ExplainResult(
        explanation="This file does X",
        citations=["docs.md"]
    )
    
    result = runner.invoke(app, ["explain", "main.py"])
    
    assert result.exit_code == 0
    assert "Explanation: main.py" in result.stdout
    assert "This file does X" in result.stdout
    assert "docs.md" in result.stdout
    mock_engine.explain.assert_called_once_with("main.py")

def test_graph_command(mock_graph):
    mock_graph.get_graph.return_value = GraphResult(
        nodes=[{"id": "A"}, {"id": "B"}],
        edges=[{"source": "A", "target": "B"}],
        citations=["graph_db"]
    )
    
    result = runner.invoke(app, ["graph"])
    
    assert result.exit_code == 0
    assert "Codebase Graph" in result.stdout
    assert "A" in result.stdout
    assert "graph_db" in result.stdout
    mock_graph.get_graph.assert_called_once()

def test_deps_command(mock_graph):
    mock_graph.get_deps.return_value = GraphResult(
        nodes=[{"id": "A"}, {"id": "B"}],
        edges=[{"source": "A", "target": "B"}],
        citations=["graph_db"]
    )
    
    result = runner.invoke(app, ["deps", "A"])
    
    assert result.exit_code == 0
    assert "Dependencies: A" in result.stdout
    assert "A" in result.stdout
    mock_graph.get_deps.assert_called_once_with("A")

def test_references_command(mock_graph):
    mock_graph.get_references.return_value = GraphResult(
        nodes=[{"id": "A"}, {"id": "B"}],
        edges=[{"source": "A", "target": "B"}],
        citations=["graph_db"]
    )
    
    result = runner.invoke(app, ["references", "A"])
    
    assert result.exit_code == 0
    assert "References: A" in result.stdout
    assert "A" in result.stdout
    mock_graph.get_references.assert_called_once_with("A")
