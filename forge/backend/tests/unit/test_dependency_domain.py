"""Unit tests for dependency domain value objects."""
import pytest

from forge.domain.code.value_objects.dependency_type import DependencyType
from forge.domain.code.value_objects.dependency_edge import DependencyEdge


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
