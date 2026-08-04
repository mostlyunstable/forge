"""DependencyType value object."""

from enum import StrEnum


class DependencyType(StrEnum):
    """Classification of code dependencies."""

    IMPORT = "import"
    FROM_IMPORT = "from_import"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    CALLS = "calls"
    TYPE_REFERENCE = "type_reference"
