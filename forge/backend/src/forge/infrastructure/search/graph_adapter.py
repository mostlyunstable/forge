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


class InMemoryDependencyGraph(IDependencyGraph):
    """In-memory graph for dependency analysis.

    Scalability note: This implementation loads the entire dependency graph
    into memory. For repositories with >100k files, consider a graph database
    (Neo4j, Neptune) or Redis-backed graph (RedisGraph).
    """

    def __init__(self) -> None:
        self._forward: dict[str, list[DependencyEdge]] = defaultdict(list)
        self._reverse: dict[str, list[DependencyEdge]] = defaultdict(list)
        self._entries_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._parser = TreeSitterParser()

    async def build(
        self,
        project_id: ProjectId,
        indexed_files: list[dict[str, Any]],
    ) -> None:
        """Build dependency graph from indexed file data."""
        self._forward.clear()
        self._reverse.clear()
        self._entries_by_file.clear()

        for file_data in indexed_files:
            file_path = file_data.get("file_path", "")
            content = file_data.get("content", "")
            entries = file_data.get("entries", [])
            self._entries_by_file[file_path] = entries

            dependencies = self._parser.extract_dependencies(file_path, content)
            for dep in dependencies:
                target_file = self._resolve_import_path(file_path, dep.target_module)
                edge = DependencyEdge(
                    source_file=file_path,
                    source_name=dep.target_name,
                    target_file=target_file,
                    target_name=dep.target_name,
                    dependency_type=dep.dependency_type,
                    line_number=dep.line_number,
                )
                self._forward[file_path].append(edge)
                self._reverse[target_file].append(edge)

    def _resolve_import_path(self, source_file: str, module_name: str) -> str:
        """Resolve a module import to a file path."""
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
        """Get direct imports from a file."""
        return self._forward.get(file_path, [])

    async def get_dependents(self, project_id: ProjectId, file_path: str) -> list[DependencyEdge]:
        """Get files that import this file."""
        return self._reverse.get(file_path, [])

    async def get_transitive_imports(self, project_id: ProjectId, file_path: str) -> list[DependencyEdge]:
        """Get all transitive imports (BFS)."""
        visited: set[str] = set()
        queue = [file_path]
        result: list[DependencyEdge] = []

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            for edge in self._forward.get(current, []):
                if edge.target_file not in visited:
                    result.append(edge)
                    queue.append(edge.target_file)

        return result

    async def get_reverse_transitive(self, project_id: ProjectId, file_path: str) -> list[DependencyEdge]:
        """Get all reverse transitive dependents (BFS)."""
        visited: set[str] = set()
        queue = [file_path]
        result: list[DependencyEdge] = []

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            for edge in self._reverse.get(current, []):
                if edge.source_file not in visited:
                    result.append(edge)
                    queue.append(edge.source_file)

        return result

    async def detect_cycles(self, project_id: ProjectId) -> list[list[str]]:
        """Detect circular dependencies using DFS."""
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for edge in self._forward.get(node, []):
                if edge.target_file not in visited:
                    dfs(edge.target_file)
                elif edge.target_file in rec_stack:
                    cycle_start = path.index(edge.target_file)
                    cycles.append(path[cycle_start:] + [edge.target_file])

            path.pop()
            rec_stack.discard(node)

        all_files = set(self._forward.keys()) | set(self._reverse.keys())
        for file_path in all_files:
            if file_path not in visited:
                dfs(file_path)

        return cycles

    async def get_statistics(self, project_id: ProjectId) -> dict[str, Any]:
        """Get graph statistics."""
        all_files = set(self._forward.keys()) | set(self._reverse.keys())
        total_edges = sum(len(edges) for edges in self._forward.values())

        return {
            "total_files": len(all_files),
            "total_dependencies": total_edges,
            "files_with_imports": len(self._forward),
            "files_imported": len(self._reverse),
        }
