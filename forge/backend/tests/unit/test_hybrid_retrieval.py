import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from forge.infrastructure.search.context_retriever import ContextRetriever

@pytest.mark.asyncio
async def test_hybrid_retrieval_with_graph_traversal():
    mock_vector_store = AsyncMock()
    mock_vector_store.search_code.return_value = [
        {
            "id": "1",
            "score": 0.8,
            "payload": {
                "file_path": "src/main.py",
                "name": "main",
                "content": "def main(): pass"
            }
        }
    ]
    mock_vector_store.search_decisions.return_value = []
    mock_vector_store.search_bugs.return_value = []

    mock_graph = AsyncMock()
    # Mock imports
    edge_mock = MagicMock()
    edge_mock.target_file = "src/utils.py"
    edge_mock.dependency_type = "IMPORT"
    mock_graph.get_imports.return_value = [edge_mock]
    mock_graph.get_dependents.return_value = []

    retriever = ContextRetriever(vector_store=mock_vector_store, dependency_graph=mock_graph)
    
    project_id = uuid4()
    context = await retriever.retrieve("how does main work?", project_id)
    
    code_results = context["relevant_code"]
    assert len(code_results) == 2 # 1 semantic + 1 graph neighbor
    
    files_in_results = {res["payload"]["file_path"] for res in code_results}
    assert "src/main.py" in files_in_results
    assert "src/utils.py" in files_in_results
