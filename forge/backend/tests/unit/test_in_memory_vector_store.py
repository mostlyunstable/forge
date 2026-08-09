import uuid

import pytest

from forge.infrastructure.search.in_memory_vector_store import InMemoryVectorStore


@pytest.fixture
def store():
    return InMemoryVectorStore()

@pytest.mark.asyncio
async def test_init_collections(store):
    await store.init_collections()
    assert "code" in store._store

@pytest.mark.asyncio
async def test_upsert_and_search_code(store):
    project_id = uuid.uuid4()

    # Insert code A
    await store.upsert_code(
        project_id=project_id,
        file_path="main.py",
        entry_type="function",
        name="hello",
        content="def hello(): pass",
        embedding=[1.0, 0.0],
        metadata={"line": 1}
    )

    # Insert code B
    await store.upsert_code(
        project_id=project_id,
        file_path="utils.py",
        entry_type="function",
        name="bye",
        content="def bye(): pass",
        embedding=[0.0, 1.0],
        metadata={"line": 5}
    )

    # Search for something closer to A
    res = await store.search_code([0.9, 0.1], project_id=project_id, limit=1)
    assert len(res) == 1
    assert res[0]["payload"]["name"] == "hello"

    # Search for something closer to B
    res2 = await store.search_code([0.1, 0.9], project_id=project_id, limit=2)
    assert len(res2) == 2
    assert res2[0]["payload"]["name"] == "bye"
    assert res2[1]["payload"]["name"] == "hello"

@pytest.mark.asyncio
async def test_upsert_and_search_decisions(store):
    project_id = uuid.uuid4()
    decision_id = uuid.uuid4()

    await store.upsert_decision(
        project_id=project_id,
        decision_id=decision_id,
        title="Use Python",
        decision="We will use Python",
        reason="It's easy",
        embedding=[1.0, 0.0]
    )

    res = await store.search_decisions([1.0, 0.0], project_id=project_id, limit=10)
    assert len(res) == 1
    assert res[0]["payload"]["title"] == "Use Python"

@pytest.mark.asyncio
async def test_upsert_and_search_bugs(store):
    project_id = uuid.uuid4()
    bug_id = uuid.uuid4()

    await store.upsert_bug(
        project_id=project_id,
        bug_id=bug_id,
        title="Crash on startup",
        problem="It crashes",
        solution="Fix it",
        embedding=[1.0, 0.0]
    )

    res = await store.search_bugs([1.0, 0.0], project_id=project_id, limit=10)
    assert len(res) == 1
    assert res[0]["payload"]["title"] == "Crash on startup"

@pytest.mark.asyncio
async def test_search_with_no_project_id_filter(store):
    pid1 = uuid.uuid4()
    pid2 = uuid.uuid4()

    await store.upsert_code(pid1, "main.py", "func", "f1", "c", [1.0, 0.0], {})
    await store.upsert_code(pid2, "app.py", "func", "f2", "c", [0.0, 1.0], {})

    res = await store.search_code([1.0, 1.0])
    assert len(res) == 2

@pytest.mark.asyncio
async def test_delete_by_project(store):
    pid1 = uuid.uuid4()
    pid2 = uuid.uuid4()

    await store.upsert_code(pid1, "main.py", "func", "f1", "c", [1.0], {})
    await store.upsert_code(pid2, "app.py", "func", "f2", "c", [1.0], {})

    await store.delete_by_project(pid1)

    assert len(store._store["code"]) == 1
    assert list(store._store["code"].values())[0]["payload"]["project_id"] == str(pid2)

@pytest.mark.asyncio
async def test_search_error(store):
    pid = uuid.uuid4()
    await store.upsert_code(pid, "main.py", "func", "f1", "c", [1.0, 0.0], {})

    # Query with mismatched dimension causes cosine similarity to return 0.0. Wait, mismatched len returns 0.0, it won't crash.
    # To trigger an exception in _search, we can mess with the internal state.
    store._store["code"][list(store._store["code"].keys())[0]]["vector"] = None

    with pytest.raises(TypeError):
        await store.search_code([1.0, 0.0])

def test_cosine_similarity(store):
    # Identical
    assert store._cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0

    # Orthogonal
    assert store._cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0

    # Opposite
    assert store._cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == -1.0

    # Mismatched length
    assert store._cosine_similarity([1.0], [1.0, 0.0]) == 0.0

    # Zero norm A
    assert store._cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0

    # Zero norm B
    assert store._cosine_similarity([1.0, 0.0], [0.0, 0.0]) == 0.0
