"""GetCallGraphUseCase - retrieves call graph for an entry."""

from __future__ import annotations

from dataclasses import dataclass, field

from forge.domain.code.repository_contracts.dependency_graph import IDependencyGraph
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class CallNode:
    file_path: str
    entry_name: str
    line_number: int


@dataclass
class GetCallGraphResponse:
    entry_name: str
    calls: list[CallNode] = field(default_factory=list)
    called_by: list[CallNode] = field(default_factory=list)


class GetCallGraphUseCase:
    """Retrieves the call graph for a specific entry."""

    def __init__(self, dependency_graph: IDependencyGraph) -> None:
        self._dependency_graph = dependency_graph

    async def execute(self, project_id: str, entry_name: str) -> GetCallGraphResponse:
        pid = ProjectId.from_string(project_id)

        all_edges = await self._dependency_graph.get_imports(pid, "")
        reverse_edges = await self._dependency_graph.get_reverse_transitive(pid, "")

        calls = [
            CallNode(
                file_path=e.source_file,
                entry_name=e.target_name,
                line_number=e.line_number,
            )
            for e in all_edges
            if e.source_name == entry_name or entry_name in e.source_name
        ]

        called_by = [
            CallNode(
                file_path=e.source_file,
                entry_name=e.source_name,
                line_number=e.line_number,
            )
            for e in reverse_edges
            if e.target_name == entry_name or entry_name in e.target_name
        ]

        return GetCallGraphResponse(
            entry_name=entry_name,
            calls=calls,
            called_by=called_by,
        )
