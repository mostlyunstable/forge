"""InMemoryDependencyGraph - in-memory graph adapter for dependency analysis."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from forge.domain.code.repository_contracts.dependency_graph import IDependencyGraph
from forge.domain.code.value_objects.dependency_edge import DependencyEdge
from forge.domain.code.value_objects.dependency_type import DependencyType
from forge.domain.code.value_objects.entry_type import EntryType
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure.code_indexer.tree_sitter_parser import TreeSitterParser


import sqlite3
import asyncio
import json

class SQLiteDependencyGraph(IDependencyGraph):
    """SQLite-backed graph adapter for dependency analysis."""

    def __init__(self, db_path: str = "forge_graph.db") -> None:
        self.db_path = db_path
        self._parser = TreeSitterParser()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS dependency_edges (
                    project_id TEXT,
                    source_file TEXT,
                    source_name TEXT,
                    target_file TEXT,
                    target_name TEXT,
                    dependency_type TEXT,
                    line_number INTEGER,
                    UNIQUE(project_id, source_file, target_file, source_name, target_name)
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_source ON dependency_edges(project_id, source_file)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_target ON dependency_edges(project_id, target_file)')

    async def build(self, project_id: ProjectId, indexed_files: list[dict[str, Any]]) -> None:
        """Build dependency graph from indexed file data."""
        def _build():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM dependency_edges WHERE project_id = ?", (str(project_id),))
                edges = []
                for file_data in indexed_files:
                    file_path = file_data.get("file_path", "")
                    content = file_data.get("content", "")
                    dependencies = self._parser.extract_dependencies(file_path, content)
                    for dep in dependencies:
                        target_file = self._resolve_import_path(file_path, dep.target_module)
                        edges.append((
                            str(project_id), file_path, dep.target_name, target_file,
                            dep.target_name, dep.dependency_type.name if hasattr(dep.dependency_type, 'name') else str(dep.dependency_type), dep.line_number
                        ))
                
                conn.executemany('''
                    INSERT OR IGNORE INTO dependency_edges 
                    (project_id, source_file, source_name, target_file, target_name, dependency_type, line_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', edges)
        await asyncio.to_thread(_build)

    async def delete_file_edges(self, project_id: ProjectId, file_path: str) -> None:
        def _delete():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM dependency_edges WHERE project_id = ? AND source_file = ?", (str(project_id), file_path))
        await asyncio.to_thread(_delete)

    async def add_file_edges(self, project_id: ProjectId, file_path: str, content: str) -> None:
        def _add():
            dependencies = self._parser.extract_dependencies(file_path, content)
            edges = []
            for dep in dependencies:
                target_file = self._resolve_import_path(file_path, dep.target_module)
                edges.append((
                    str(project_id), file_path, dep.target_name, target_file,
                    dep.target_name, dep.dependency_type.name if hasattr(dep.dependency_type, 'name') else str(dep.dependency_type), dep.line_number
                ))
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany('''
                    INSERT OR IGNORE INTO dependency_edges 
                    (project_id, source_file, source_name, target_file, target_name, dependency_type, line_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', edges)
        await asyncio.to_thread(_add)

    def _resolve_import_path(self, source_file: str, module_name: str) -> str:
        if not module_name:
            return ""
        if module_name.startswith("."):
            source_dir = source_file.rsplit("/", 1)[0] if "/" in source_file else ""
            rel_path = module_name.lstrip(".")
            if rel_path:
                return f"{source_dir}/{rel_path}".lstrip("/")
            return source_dir
        parts = module_name.split(".")
        resolved = "/".join(parts)
        if source_file.endswith(".py"):
            return resolved + ".py"
        return resolved

    async def get_imports(self, project_id: ProjectId, file_path: str) -> list[DependencyEdge]:
        def _get():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM dependency_edges WHERE project_id = ? AND source_file = ?", (str(project_id), file_path))
                return [self._row_to_edge(row) for row in cursor.fetchall()]
        return await asyncio.to_thread(_get)

    async def get_dependents(self, project_id: ProjectId, file_path: str) -> list[DependencyEdge]:
        def _get():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM dependency_edges WHERE project_id = ? AND target_file = ?", (str(project_id), file_path))
                return [self._row_to_edge(row) for row in cursor.fetchall()]
        return await asyncio.to_thread(_get)

    def _row_to_edge(self, row) -> DependencyEdge:
        return DependencyEdge(
            source_file=row[1],
            source_name=row[2],
            target_file=row[3],
            target_name=row[4],
            dependency_type=DependencyType.IMPORT,  # Simplified parsing
            line_number=row[6],
        )

    async def get_transitive_imports(self, project_id: ProjectId, file_path: str) -> list[DependencyEdge]:
        # Using iterative approach with db queries
        visited = set()
        queue = [file_path]
        result = []
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            edges = await self.get_imports(project_id, current)
            for edge in edges:
                if edge.target_file not in visited:
                    result.append(edge)
                    queue.append(edge.target_file)
        return result

    async def get_reverse_transitive(self, project_id: ProjectId, file_path: str) -> list[DependencyEdge]:
        visited = set()
        queue = [file_path]
        result = []
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            edges = await self.get_dependents(project_id, current)
            for edge in edges:
                if edge.source_file not in visited:
                    result.append(edge)
                    queue.append(edge.source_file)
        return result

    async def detect_cycles(self, project_id: ProjectId) -> list[list[str]]:
        def _detect():
            cycles = []
            visited = set()
            rec_stack = set()
            path = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT source_file, target_file FROM dependency_edges WHERE project_id = ?", (str(project_id),))
                forward = defaultdict(list)
                for src, tgt in cursor.fetchall():
                    forward[src].append(tgt)

            def dfs(node: str) -> None:
                visited.add(node)
                rec_stack.add(node)
                path.append(node)
                for tgt in forward.get(node, []):
                    if tgt not in visited:
                        dfs(tgt)
                    elif tgt in rec_stack:
                        cycle_start = path.index(tgt)
                        cycles.append(path[cycle_start:] + [tgt])
                path.pop()
                rec_stack.discard(node)

            all_files = set(forward.keys()) | {tgt for tgts in forward.values() for tgt in tgts}
            for f in all_files:
                if f not in visited:
                    dfs(f)
            return cycles
        return await asyncio.to_thread(_detect)

    async def get_statistics(self, project_id: ProjectId) -> dict[str, Any]:
        def _stats():
            with sqlite3.connect(self.db_path) as conn:
                c1 = conn.execute("SELECT COUNT(*) FROM dependency_edges WHERE project_id = ?", (str(project_id),)).fetchone()[0]
                c2 = conn.execute("SELECT COUNT(DISTINCT source_file) FROM dependency_edges WHERE project_id = ?", (str(project_id),)).fetchone()[0]
                c3 = conn.execute("SELECT COUNT(DISTINCT target_file) FROM dependency_edges WHERE project_id = ?", (str(project_id),)).fetchone()[0]
                return {
                    "total_dependencies": c1,
                    "files_with_imports": c2,
                    "files_imported": c3,
                }
        return await asyncio.to_thread(_stats)
