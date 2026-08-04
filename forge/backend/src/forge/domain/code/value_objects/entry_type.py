"""EntryType value object."""

from enum import StrEnum


class EntryType(StrEnum):
    """Classification of code entries extracted by Tree-sitter."""

    CLASS = "class"
    FUNCTION = "function"
    INTERFACE = "interface"
    ENUM = "enum"
    METHOD = "method"
    VARIABLE = "variable"
    MODULE = "module"
    ADR = "adr"
    MARKDOWN_SECTION = "markdown_section"
    SQL_STATEMENT = "sql_statement"
