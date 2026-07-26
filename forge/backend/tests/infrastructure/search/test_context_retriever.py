import pytest
from unittest.mock import AsyncMock, MagicMock
from forge.infrastructure.search.context_retriever import ContextRetriever

@pytest.mark.asyncio
async def test_context_retriever_retrieve():
    mock_vector_store = AsyncMock()
    mock_vector_store.search_code.return_value = [
        {"id": "code1", "payload": {"file_path": "a.py", "name": "a", "content": "hello code"}}
    ]
    mock_vector_store.search_decisions.return_value = [
        {"id": "dec1", "payload": {"title": "decision 1", "content": "we chose python"}}
    ]
    mock_vector_store.search_bugs.return_value = [
        {"id": "bug1", "payload": {"title": "bug 1", "content": "crashes on startup"}}
    ]
    
    mock_graph = AsyncMock()
    mock_graph.get_imports.return_value = []
    mock_graph.get_dependents.return_value = []
    
    retriever = ContextRetriever(vector_store=mock_vector_store, dependency_graph=mock_graph)
    retriever._embedding_service.get_embedding = AsyncMock(return_value=[0.1]*1536)
    
    project_id = MagicMock()
    project_id.value = "123"
    
    res = await retriever.retrieve("where is the code?", project_id)
    
    assert "relevant_code" in res
    assert "relevant_decisions" in res
    assert "relevant_bugs" in res
    
    assert len(res["relevant_code"]) == 1
    assert res["relevant_code"][0]["id"] == "code1"
    assert res["relevant_code"][0]["type"] == "code"
    
    assert len(res["relevant_decisions"]) == 1
    assert res["relevant_decisions"][0]["id"] == "dec1"
    assert res["relevant_decisions"][0]["type"] == "decision"
    
    assert len(res["relevant_bugs"]) == 1
    assert res["relevant_bugs"][0]["id"] == "bug1"
    assert res["relevant_bugs"][0]["type"] == "bug"

