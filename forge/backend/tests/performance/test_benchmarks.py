"""Performance benchmarks for core operations."""
import asyncio
import time
from uuid import uuid4

import pytest

from forge.domain.projects.entities.project import Project
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.value_objects.tech_stack import TechStack
from forge.infrastructure.search.graph_adapter import InMemoryDependencyGraph
from forge.infrastructure.code_indexer.tree_sitter_parser import TreeSitterParser


class TestParserPerformance:
    """Benchmarks for Tree-sitter parser."""

    def setup_method(self):
        self.parser = TreeSitterParser()

    def test_parse_python_file(self):
        content = """
def hello_world():
    return "Hello, World!"

class MyClass:
    def __init__(self):
        self.value = 42

    def method(self):
        return self.value
"""
        start = time.perf_counter()
        for _ in range(100):
            self.parser.parse_file("test.py", content)
        duration = time.perf_counter() - start
        assert duration < 1.0, f"Parsing 100 files took {duration:.2f}s"

    def test_parse_typescript_file(self):
        content = """
interface User {
    id: number;
    name: string;
}

function greet(user: User): string {
    return `Hello, ${user.name}!`;
}

class UserService {
    getUser(id: number): User {
        return { id, name: "Test" };
    }
}
"""
        start = time.perf_counter()
        for _ in range(100):
            self.parser.parse_file("test.ts", content)
        duration = time.perf_counter() - start
        assert duration < 1.0, f"Parsing 100 TS files took {duration:.2f}s"

    def test_extract_dependencies(self):
        content = "import os\nfrom sys import argv\nimport numpy as np\n"
        start = time.perf_counter()
        for _ in range(100):
            self.parser.extract_dependencies("test.py", content)
        duration = time.perf_counter() - start
        assert duration < 0.5, f"Extracting deps 100 times took {duration:.2f}s"


class TestGraphPerformance:
    """Benchmarks for dependency graph operations."""

    @pytest.mark.asyncio
    async def test_build_small_graph(self):
        graph = InMemoryDependencyGraph()
        project_id = ProjectId(uuid4())

        indexed_files = [
            {"file_path": f"file_{i}.py", "content": f"import file_{(i+1) % 10}\n", "entries": []}
            for i in range(10)
        ]

        start = time.perf_counter()
        await graph.build(project_id, indexed_files)
        duration = time.perf_counter() - start
        assert duration < 0.1, f"Building 10-node graph took {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_build_medium_graph(self):
        graph = InMemoryDependencyGraph()
        project_id = ProjectId(uuid4())

        indexed_files = [
            {"file_path": f"module_{i}.py", "content": f"import module_{(i+1) % 100}\n", "entries": []}
            for i in range(100)
        ]

        start = time.perf_counter()
        await graph.build(project_id, indexed_files)
        duration = time.perf_counter() - start
        assert duration < 0.5, f"Building 100-node graph took {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_transitive_query_performance(self):
        graph = InMemoryDependencyGraph()
        project_id = ProjectId(uuid4())

        indexed_files = [
            {"file_path": f"file_{i}.py", "content": f"import file_{i+1}\n", "entries": []}
            for i in range(50)
        ]
        await graph.build(project_id, indexed_files)

        start = time.perf_counter()
        for _ in range(100):
            await graph.get_transitive_imports(project_id, "file_0.py")
        duration = time.perf_counter() - start
        assert duration < 1.0, f"100 transitive queries took {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_cycle_detection_performance(self):
        graph = InMemoryDependencyGraph()
        project_id = ProjectId(uuid4())

        indexed_files = [
            {"file_path": f"file_{i}.py", "content": f"import file_{(i+1) % 50}\n", "entries": []}
            for i in range(50)
        ]
        await graph.build(project_id, indexed_files)

        start = time.perf_counter()
        for _ in range(10):
            await graph.detect_cycles(project_id)
        duration = time.perf_counter() - start
        assert duration < 1.0, f"10 cycle detections took {duration:.2f}s"
