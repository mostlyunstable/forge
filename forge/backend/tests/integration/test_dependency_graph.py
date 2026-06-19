"""Integration tests for dependency graph use case."""
import pytest
from uuid import uuid4

from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure.search.graph_adapter import InMemoryDependencyGraph
from forge.application.code.build_dependency_graph import BuildDependencyGraphUseCase, BuildDependencyGraphRequest
from forge.application.code.get_import_graph import GetImportGraphUseCase


@pytest.fixture
def graph():
    return InMemoryDependencyGraph()


@pytest.fixture
def project_id():
    return ProjectId(uuid4())


@pytest.mark.asyncio
async def test_build_and_query_dependency_graph(graph, project_id):
    indexed_files = [
        {
            "file_path": "src/main.py",
            "content": "from src.utils import helper\nimport os\n",
            "entries": [],
        },
        {
            "file_path": "src/utils.py",
            "content": "def helper(): pass\n",
            "entries": [],
        },
    ]

    build_use_case = BuildDependencyGraphUseCase(graph)
    result = await build_use_case.execute(
        BuildDependencyGraphRequest(
            project_id=str(project_id.value),
            indexed_files=indexed_files,
        )
    )

    assert result.total_files >= 2
    assert result.total_dependencies >= 1

    query_use_case = GetImportGraphUseCase(graph)
    import_result = await query_use_case.execute(
        project_id=str(project_id.value),
        file_path="src/main.py",
    )

    assert import_result.file_path == "src/main.py"
    assert len(import_result.direct_imports) > 0


@pytest.mark.asyncio
async def test_cycle_detection(graph, project_id):
    indexed_files = [
        {
            "file_path": "a.py",
            "content": "import b\n",
            "entries": [],
        },
        {
            "file_path": "b.py",
            "content": "import a\n",
            "entries": [],
        },
    ]

    build_use_case = BuildDependencyGraphUseCase(graph)
    result = await build_use_case.execute(
        BuildDependencyGraphRequest(
            project_id=str(project_id.value),
            indexed_files=indexed_files,
        )
    )

    assert len(result.cycles) > 0


@pytest.mark.asyncio
async def test_transitive_dependencies(graph, project_id):
    indexed_files = [
        {
            "file_path": "a.py",
            "content": "import b\n",
            "entries": [],
        },
        {
            "file_path": "b.py",
            "content": "import c\n",
            "entries": [],
        },
        {
            "file_path": "c.py",
            "content": "x = 1\n",
            "entries": [],
        },
    ]

    build_use_case = BuildDependencyGraphUseCase(graph)
    await build_use_case.execute(
        BuildDependencyGraphRequest(
            project_id=str(project_id.value),
            indexed_files=indexed_files,
        )
    )

    query_use_case = GetImportGraphUseCase(graph)
    result = await query_use_case.execute(
        project_id=str(project_id.value),
        file_path="a.py",
    )

    assert len(result.transitive_imports) >= 1
