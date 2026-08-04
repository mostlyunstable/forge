"""GetImportGraphUseCase - retrieves import graph for a file."""

from __future__ import annotations

from dataclasses import dataclass, field

from forge.domain.code.repository_contracts.dependency_graph import IDependencyGraph
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class ImportNode:
    file_path: str
    imports: list[str] = field(default_factory=list)
    line_numbers: list[int] = field(default_factory=list)


@dataclass
class GetImportGraphResponse:
    file_path: str
    direct_imports: list[ImportNode]
    transitive_imports: list[ImportNode]
    imported_by: list[ImportNode]


class GetImportGraphUseCase:
    """Retrieves the import graph for a specific file."""

    def __init__(self, dependency_graph: IDependencyGraph) -> None:
        self._dependency_graph = dependency_graph

    async def execute(self, project_id: str, file_path: str) -> GetImportGraphResponse:
        pid = ProjectId.from_string(project_id)

        direct = await self._dependency_graph.get_imports(pid, file_path)
        transitive = await self._dependency_graph.get_transitive_imports(pid, file_path)
        reverse = await self._dependency_graph.get_reverse_transitive(pid, file_path)

        direct_nodes = self._group_by_file(direct, "target_file")
        transitive_nodes = self._group_by_file(transitive, "target_file")
        reverse_nodes = self._group_by_file(reverse, "source_file")

        return GetImportGraphResponse(
            file_path=file_path,
            direct_imports=direct_nodes,
            transitive_imports=transitive_nodes,
            imported_by=reverse_nodes,
        )

    def _group_by_file(self, edges: list, field_name: str) -> list[ImportNode]:
        file_map: dict[str, ImportNode] = {}
        for edge in edges:
            file_path = getattr(edge, field_name)
            if file_path not in file_map:
                file_map[file_path] = ImportNode(file_path=file_path)
            file_map[file_path].imports.append(edge.target_name)
            file_map[file_path].line_numbers.append(edge.line_number)
        return list(file_map.values())
