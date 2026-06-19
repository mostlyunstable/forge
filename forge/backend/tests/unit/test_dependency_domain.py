"""Unit tests for dependency domain entities and value objects."""
import pytest
from uuid import uuid4

from forge.domain.code.value_objects.dependency_type import DependencyType
from forge.domain.code.value_objects.dependency_edge import DependencyEdge
from forge.domain.code.entities.code_dependency import CodeDependency
from forge.domain.projects.value_objects.project_id import ProjectId


def test_dependency_type_enum():
    assert DependencyType.IMPORT == "import"
    assert DependencyType.FROM_IMPORT == "from_import"
    assert DependencyType.EXTENDS == "extends"
    assert DependencyType.IMPLEMENTS == "implements"
    assert DependencyType.CALLS == "calls"
    assert DependencyType.TYPE_REFERENCE == "type_reference"


def test_dependency_edge_creation():
    edge = DependencyEdge(
        source_file="src/main.py",
        source_name="utils",
        target_file="src/utils.py",
        target_name="utils",
        dependency_type=DependencyType.IMPORT,
        line_number=1,
    )
    assert edge.source_file == "src/main.py"
    assert edge.target_file == "src/utils.py"
    assert edge.line_number == 1


def test_dependency_edge_validation():
    with pytest.raises(ValueError):
        DependencyEdge(
            source_file="",
            source_name="x",
            target_file="y.py",
            target_name="y",
            dependency_type=DependencyType.IMPORT,
            line_number=1,
        )


def test_dependency_edge_negative_line():
    with pytest.raises(ValueError):
        DependencyEdge(
            source_file="a.py",
            source_name="x",
            target_file="b.py",
            target_name="y",
            dependency_type=DependencyType.IMPORT,
            line_number=-1,
        )


def test_code_dependency_create():
    dep = CodeDependency.create(
        project_id=ProjectId(uuid4()),
        source_entry_id=uuid4(),
        target_entry_id=uuid4(),
        dependency_type=DependencyType.IMPORT,
        source_file="src/main.py",
        target_file="src/utils.py",
        line_number=5,
    )
    assert dep.source_file == "src/main.py"
    assert dep.target_file == "src/utils.py"
    assert dep.dependency_type == DependencyType.IMPORT
    assert dep.line_number == 5


def test_code_dependency_optional_target():
    dep = CodeDependency.create(
        project_id=ProjectId(uuid4()),
        source_entry_id=uuid4(),
        target_entry_id=None,
        dependency_type=DependencyType.IMPORT,
        source_file="src/main.py",
        target_file="os",
        line_number=1,
    )
    assert dep.target_entry_id is None
