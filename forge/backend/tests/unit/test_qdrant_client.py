import asyncio
import uuid
from unittest.mock import patch, MagicMock

import pytest
from qdrant_client.models import PointStruct, Filter

from forge.infrastructure.search.qdrant_client import QdrantVectorStore, COLLECTIONS

@pytest.fixture
def store():
    return QdrantVectorStore()

@pytest.fixture
def mock_qdrant():
    with patch("forge.infrastructure.search.qdrant_client.QdrantClient") as MockClient:
        client = MagicMock()
        MockClient.return_value = client
        yield client

@pytest.mark.asyncio
async def test_init_collections_create(store, mock_qdrant):
    mock_qdrant.get_collection.side_effect = Exception("Not found")
    await store.init_collections()
    assert mock_qdrant.get_collection.call_count == 3
    assert mock_qdrant.create_collection.call_count == 3

@pytest.mark.asyncio
async def test_init_collections_existing(store, mock_qdrant):
    await store.init_collections()
    assert mock_qdrant.get_collection.call_count == 3
    assert mock_qdrant.create_collection.call_count == 0

@pytest.mark.asyncio
async def test_upsert_code(store, mock_qdrant):
    pid = uuid.uuid4()
    await store.upsert_code(pid, "main.py", "function", "func_name", "def foo(): pass", [0.1, 0.2], {})
    mock_qdrant.upsert.assert_called_once()
    args, kwargs = mock_qdrant.upsert.call_args
    assert kwargs["collection_name"] == COLLECTIONS["code"]
    assert len(kwargs["points"]) == 1
    point = kwargs["points"][0]
    assert point.payload["project_id"] == str(pid)

@pytest.mark.asyncio
async def test_upsert_decision(store, mock_qdrant):
    pid = uuid.uuid4()
    did = uuid.uuid4()
    await store.upsert_decision(pid, did, "Title", "Decision", "Reason", [0.1, 0.2])
    mock_qdrant.upsert.assert_called_once()
    args, kwargs = mock_qdrant.upsert.call_args
    assert kwargs["collection_name"] == COLLECTIONS["decisions"]

@pytest.mark.asyncio
async def test_upsert_bug(store, mock_qdrant):
    pid = uuid.uuid4()
    bid = uuid.uuid4()
    await store.upsert_bug(pid, bid, "Bug", "Problem", "Solution", [0.1, 0.2])
    mock_qdrant.upsert.assert_called_once()
    args, kwargs = mock_qdrant.upsert.call_args
    assert kwargs["collection_name"] == COLLECTIONS["bugs"]

@pytest.mark.asyncio
async def test_search_code(store, mock_qdrant):
    pid = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.id = 1
    mock_result.score = 0.99
    mock_result.payload = {"file_path": "main.py"}
    
    mock_query_result = MagicMock()
    mock_query_result.points = [mock_result]
    mock_qdrant.query_points.return_value = mock_query_result

    res = await store.search_code([0.1, 0.2], project_id=pid, limit=1)
    assert len(res) == 1
    assert res[0]["id"] == 1
    assert res[0]["score"] == 0.99
    mock_qdrant.query_points.assert_called_once()

@pytest.mark.asyncio
async def test_search_code_failure(store, mock_qdrant):
    mock_qdrant.query_points.side_effect = Exception("error")
    with pytest.raises(Exception):
        await store.search_code([0.1, 0.2])

@pytest.mark.asyncio
async def test_search_decisions(store, mock_qdrant):
    mock_result = MagicMock()
    mock_result.id = "did"
    mock_result.score = 0.9
    mock_result.payload = {}
    mock_query_result = MagicMock()
    mock_query_result.points = [mock_result]
    mock_qdrant.query_points.return_value = mock_query_result

    res = await store.search_decisions([0.1], limit=1)
    assert len(res) == 1
    assert res[0]["id"] == "did"

@pytest.mark.asyncio
async def test_search_decisions_failure(store, mock_qdrant):
    mock_qdrant.query_points.side_effect = Exception("error")
    with pytest.raises(Exception):
        await store.search_decisions([0.1])

@pytest.mark.asyncio
async def test_search_bugs(store, mock_qdrant):
    mock_result = MagicMock()
    mock_result.id = "bid"
    mock_result.score = 0.8
    mock_result.payload = {}
    mock_query_result = MagicMock()
    mock_query_result.points = [mock_result]
    mock_qdrant.query_points.return_value = mock_query_result

    res = await store.search_bugs([0.1], limit=1)
    assert len(res) == 1
    assert res[0]["id"] == "bid"

@pytest.mark.asyncio
async def test_search_bugs_failure(store, mock_qdrant):
    mock_qdrant.query_points.side_effect = Exception("error")
    with pytest.raises(Exception):
        await store.search_bugs([0.1])

@pytest.mark.asyncio
async def test_delete_by_project(store, mock_qdrant):
    pid = uuid.uuid4()
    await store.delete_by_project(pid)
    assert mock_qdrant.delete.call_count == 3

@pytest.mark.asyncio
async def test_delete_by_file(store, mock_qdrant):
    pid = uuid.uuid4()
    await store.delete_by_file(pid, "main.py")
    mock_qdrant.delete.assert_called_once()
