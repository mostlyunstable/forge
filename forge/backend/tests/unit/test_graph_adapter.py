"""Unit tests for SQLiteDependencyGraph."""
import pytest
import asyncio

from uuid import uuid4

from forge.domain.code.value_objects.dependency_type import DependencyType
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure.search.graph_adapter import SQLiteDependencyGraph


@pytest.fixture
def graph():
    return SQLiteDependencyGraph()


@pytest.fixture
def project_id():
    return ProjectId(uuid4())


class TestSQLiteDependencyGraph:
    @pytest.mark.asyncio
    async def test_build_from_files(self, graph, project_id):
        indexed_files = [
            {
                "file_path": "src/main.py",
                "content": "import os\nimport sys\n",
                "entries": [],
            },
            {
                "file_path": "src/utils.py",
                "content": "def helper(): pass\n",
                "entries": [],
            },
        ]
        await graph.build(project_id, indexed_files)
        stats = await graph.get_statistics(project_id)
        assert stats["files_with_imports"] >= 1

    @pytest.mark.asyncio
    async def test_get_imports(self, graph, project_id):
        indexed_files = [
            {
                "file_path": "src/main.py",
                "content": "import os\n",
                "entries": [],
            },
        ]
        await graph.build(project_id, indexed_files)
        imports = await graph.get_imports(project_id, "src/main.py")
        assert len(imports) > 0
        assert imports[0].source_file == "src/main.py"

    @pytest.mark.asyncio
    async def test_get_dependents(self, graph, project_id):
        indexed_files = [
            {
                "file_path": "src/main.py",
                "content": "from src.utils import helper\n",
                "entries": [],
            },
            {
                "file_path": "src/utils.py",
                "content": "def helper(): pass\n",
                "entries": [],
            },
        ]
        await graph.build(project_id, indexed_files)
        dependents = await graph.get_dependents(project_id, "src/utils.py")
        assert len(dependents) > 0

    @pytest.mark.asyncio
    async def test_transitive_imports(self, graph, project_id):
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
        await graph.build(project_id, indexed_files)
        transitive = await graph.get_transitive_imports(project_id, "a.py")
        assert len(transitive) >= 1

    @pytest.mark.asyncio
    async def test_detect_cycles(self, graph, project_id):
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
        await graph.build(project_id, indexed_files)
        cycles = await graph.detect_cycles(project_id)
        assert len(cycles) > 0

    @pytest.mark.asyncio
    async def test_statistics(self, graph, project_id):
        indexed_files = [
            {
                "file_path": "main.py",
                "content": "import os\n",
                "entries": [],
            },
        ]
        await graph.build(project_id, indexed_files)
        stats = await graph.get_statistics(project_id)
        assert "files_with_imports" in stats
        assert "total_dependencies" in stats
