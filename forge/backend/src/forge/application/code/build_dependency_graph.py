"""BuildDependencyGraphUseCase - builds dependency graph from indexed code."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from forge.domain.code.repository_contracts.dependency_graph import IDependencyGraph
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class BuildDependencyGraphRequest:
    project_id: str
    indexed_files: list[dict[str, Any]]


@dataclass
class BuildDependencyGraphResponse:
    total_files: int
    total_dependencies: int
    files_with_imports: int
    files_imported: int
    cycles: list[list[str]]


class BuildDependencyGraphUseCase:
    """Builds a dependency graph from indexed code entries."""

    def __init__(self, dependency_graph: IDependencyGraph) -> None:
        self._dependency_graph = dependency_graph

    async def execute(self, request: BuildDependencyGraphRequest) -> BuildDependencyGraphResponse:
        project_id = ProjectId.from_string(request.project_id)

        await self._dependency_graph.build(project_id, request.indexed_files)

        stats = await self._dependency_graph.get_statistics(project_id)
        cycles = await self._dependency_graph.detect_cycles(project_id)

        return BuildDependencyGraphResponse(
            total_files=stats["total_files"],
            total_dependencies=stats["total_dependencies"],
            files_with_imports=stats["files_with_imports"],
            files_imported=stats["files_imported"],
            cycles=cycles,
        )
