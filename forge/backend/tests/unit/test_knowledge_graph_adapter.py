"""Tests for Knowledge Graph SQLite adapter."""
import pytest
import uuid
from datetime import datetime, timezone

from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.knowledge_graph.entities.relationship import Relationship, RelationshipType
from forge.infrastructure.knowledge_graph.graph_adapter import SQLiteGraphAdapter

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_kg.db")

@pytest.fixture
def adapter(db_path):
    return SQLiteGraphAdapter(db_path=db_path)

@pytest.fixture
def project_id():
    return ProjectId(uuid.uuid4())

@pytest.mark.asyncio
async def test_add_and_get_relationships(adapter, project_id):
    rel = Relationship.create(
        project_id=project_id,
        source_id="file1.py",
        target_id="file2.py",
        relationship_type=RelationshipType.REFERENCES,
        metadata={"line": 10}
    )
    await adapter.add_relationships(project_id, [rel])
    
    rels = await adapter.get_relationships(project_id, source_id="file1.py")
    assert len(rels) == 1
    assert rels[0].source_id == "file1.py"
    assert rels[0].target_id == "file2.py"
    assert rels[0].relationship_type == RelationshipType.REFERENCES
    assert rels[0].metadata == {"line": 10}

@pytest.mark.asyncio
async def test_traverse_multihop(adapter, project_id):
    r1 = Relationship.create(
        project_id=project_id, source_id="A", target_id="B", relationship_type=RelationshipType.DEPENDS_ON
    )
    r2 = Relationship.create(
        project_id=project_id, source_id="B", target_id="C", relationship_type=RelationshipType.DEPENDS_ON
    )
    await adapter.add_relationships(project_id, [r1, r2])
    
    path = await adapter.traverse(project_id, start_id="A", max_depth=2, direction="outbound")
    
    # Node B should be at depth 1, Node C at depth 2
    assert len(path) == 2
    depths = {p["target_id"]: p["depth"] for p in path}
    assert depths["B"] == 1
    assert depths["C"] == 2

@pytest.mark.asyncio
async def test_delete_relationships(adapter, project_id):
    r1 = Relationship.create(
        project_id=project_id, source_id="X", target_id="Y", relationship_type=RelationshipType.AFFECTS
    )
    await adapter.add_relationships(project_id, [r1])
    
    await adapter.delete_relationships_for_source(project_id, "X")
    rels = await adapter.get_relationships(project_id, source_id="X")
    assert len(rels) == 0
