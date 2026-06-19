"""DependencyType value object."""
from enum import Enum


class DependencyType(str, Enum):
    """Classification of code dependencies."""

    IMPORT = "import"
    FROM_IMPORT = "from_import"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    CALLS = "calls"
    TYPE_REFERENCE = "type_reference"
