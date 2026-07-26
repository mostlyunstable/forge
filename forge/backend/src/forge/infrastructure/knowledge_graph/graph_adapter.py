"""SQLite graph adapter implementation."""
from __future__ import annotations

import asyncio
import json
import sqlite3
import uuid
from typing import Any

from forge.domain.knowledge_graph.entities.relationship import Relationship, RelationshipType
from forge.domain.knowledge_graph.repository_contracts.graph_adapter import IGraphAdapter
from forge.domain.projects.value_objects.project_id import ProjectId

class SQLiteGraphAdapter(IGraphAdapter):
    """SQLite-backed graph adapter for the generic knowledge graph."""
    
    def __init__(self, db_path: str = "forge_knowledge_graph.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS relationships (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    source_id TEXT,
                    target_id TEXT,
                    relationship_type TEXT,
                    metadata TEXT,
                    created_at TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_kg_source ON relationships(project_id, source_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_kg_target ON relationships(project_id, target_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_kg_type ON relationships(project_id, relationship_type)')

    async def add_relationships(self, project_id: ProjectId, relationships: list[Relationship]) -> None:
        def _add():
            with sqlite3.connect(self.db_path) as conn:
                edges = [
                    (
                        str(r.id),
                        str(r.project_id),
                        r.source_id,
                        r.target_id,
                        r.relationship_type.value,
                        json.dumps(r.metadata),
                        r.created_at.isoformat()
                    )
                    for r in relationships
                ]
                conn.executemany('''
                    INSERT OR REPLACE INTO relationships 
                    (id, project_id, source_id, target_id, relationship_type, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', edges)
        await asyncio.to_thread(_add)

    async def delete_relationships_for_source(self, project_id: ProjectId, source_id: str) -> None:
        def _delete():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM relationships WHERE project_id = ? AND source_id = ?", 
                    (str(project_id), source_id)
                )
        await asyncio.to_thread(_delete)

    async def get_relationships(
        self, 
        project_id: ProjectId, 
        source_id: str | None = None, 
        target_id: str | None = None,
        relationship_type: RelationshipType | None = None
    ) -> list[Relationship]:
        def _get():
            query = "SELECT id, project_id, source_id, target_id, relationship_type, metadata, created_at FROM relationships WHERE project_id = ?"
            params = [str(project_id)]
            
            if source_id:
                query += " AND source_id = ?"
                params.append(source_id)
            if target_id:
                query += " AND target_id = ?"
                params.append(target_id)
            if relationship_type:
                query += " AND relationship_type = ?"
                params.append(relationship_type.value)
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, tuple(params))
                from datetime import datetime
                results = []
                for row in cursor.fetchall():
                    results.append(Relationship(
                        id=uuid.UUID(row[0]),
                        project_id=ProjectId(uuid.UUID(row[1])),
                        source_id=row[2],
                        target_id=row[3],
                        relationship_type=RelationshipType(row[4]),
                        metadata=json.loads(row[5]) if row[5] else {},
                        created_at=datetime.fromisoformat(row[6])
                    ))
                return results
        return await asyncio.to_thread(_get)

    async def traverse(
        self,
        project_id: ProjectId,
        start_id: str,
        max_depth: int = 1,
        relationship_types: list[RelationshipType] | None = None,
        direction: str = "outbound"
    ) -> list[dict[str, Any]]:
        def _traverse():
            visited = set()
            queue = [(start_id, 0)]
            results = []
            
            with sqlite3.connect(self.db_path) as conn:
                while queue:
                    current_id, current_depth = queue.pop(0)
                    
                    if current_depth >= max_depth:
                        continue
                        
                    if current_id in visited:
                        continue
                    visited.add(current_id)
                    
                    query = "SELECT id, source_id, target_id, relationship_type, metadata FROM relationships WHERE project_id = ?"
                    params = [str(project_id)]
                    
                    if direction == "outbound":
                        query += " AND source_id = ?"
                        params.append(current_id)
                    elif direction == "inbound":
                        query += " AND target_id = ?"
                        params.append(current_id)
                    else: # both
                        query += " AND (source_id = ? OR target_id = ?)"
                        params.extend([current_id, current_id])
                        
                    if relationship_types:
                        type_placeholders = ",".join(["?"] * len(relationship_types))
                        query += f" AND relationship_type IN ({type_placeholders})"
                        params.extend([rt.value for rt in relationship_types])
                        
                    cursor = conn.execute(query, tuple(params))
                    
                    for row in cursor.fetchall():
                        r_id, src, tgt, r_type, meta = row
                        
                        results.append({
                            "id": r_id,
                            "source_id": src,
                            "target_id": tgt,
                            "relationship_type": r_type,
                            "metadata": json.loads(meta) if meta else {},
                            "depth": current_depth + 1
                        })
                        
                        next_id = tgt if current_id == src else src
                        if next_id not in visited:
                            queue.append((next_id, current_depth + 1))
                            
            return results
        return await asyncio.to_thread(_traverse)
