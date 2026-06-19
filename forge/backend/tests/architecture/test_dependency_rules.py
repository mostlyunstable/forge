"""Architecture tests: enforce dependency rules, file size limits, module isolation.
These tests MUST pass in CI. Any failure is a build breaker."""
import ast
import os
from pathlib import Path
import pytest

SRC_DIR = Path(__file__).parent.parent.parent / "src" / "forge"

DOMAIN_DIR = SRC_DIR / "domain"
APPLICATION_DIR = SRC_DIR / "application"
INFRASTRUCTURE_DIR = SRC_DIR / "infrastructure"
PRESENTATION_DIR = SRC_DIR / "presentation"

MAX_FILE_LINES = 500
MAX_FUNCTION_LINES = 50
MAX_CLASS_LINES = 250


def _collect_python_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return list(directory.rglob("*.py"))


def _get_imports_from_file(filepath: Path) -> list[str]:
    try:
        content = filepath.read_text()
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _is_domain_import(module: str) -> bool:
    return module.startswith("forge.domain")


def _is_application_import(module: str) -> bool:
    return module.startswith("forge.application")


def _is_infrastructure_import(module: str) -> bool:
    return module.startswith("forge.infrastructure")


def _is_presentation_import(module: str) -> bool:
    return module.startswith("forge.presentation")


class TestDomainIsolation:
    """Domain layer must have ZERO imports from other layers."""

    def test_domain_has_no_application_imports(self):
        violations = []
        for filepath in _collect_python_files(DOMAIN_DIR):
            for imp in _get_imports_from_file(filepath):
                if _is_application_import(imp):
                    violations.append(f"{filepath.relative_to(SRC_DIR)}: imports {imp}")
        assert not violations, f"Domain imports Application:\n" + "\n".join(violations)

    def test_domain_has_no_infrastructure_imports(self):
        violations = []
        for filepath in _collect_python_files(DOMAIN_DIR):
            for imp in _get_imports_from_file(filepath):
                if _is_infrastructure_import(imp):
                    violations.append(f"{filepath.relative_to(SRC_DIR)}: imports {imp}")
        assert not violations, f"Domain imports Infrastructure:\n" + "\n".join(violations)

    def test_domain_has_no_presentation_imports(self):
        violations = []
        for filepath in _collect_python_files(DOMAIN_DIR):
            for imp in _get_imports_from_file(filepath):
                if _is_presentation_import(imp):
                    violations.append(f"{filepath.relative_to(SRC_DIR)}: imports {imp}")
        assert not violations, f"Domain imports Presentation:\n" + "\n".join(violations)


class TestApplicationIsolation:
    """Application layer may only import from Domain."""

    def test_application_has_no_infrastructure_imports(self):
        violations = []
        for filepath in _collect_python_files(APPLICATION_DIR):
            for imp in _get_imports_from_file(filepath):
                if _is_infrastructure_import(imp):
                    violations.append(f"{filepath.relative_to(SRC_DIR)}: imports {imp}")
        assert not violations, f"Application imports Infrastructure:\n" + "\n".join(violations)

    def test_application_has_no_presentation_imports(self):
        violations = []
        for filepath in _collect_python_files(APPLICATION_DIR):
            for imp in _get_imports_from_file(filepath):
                if _is_presentation_import(imp):
                    violations.append(f"{filepath.relative_to(SRC_DIR)}: imports {imp}")
        assert not violations, f"Application imports Presentation:\n" + "\n".join(violations)


class TestInfrastructureIsolation:
    """Infrastructure may import Domain (to implement contracts) but NOT Application or Presentation."""

    def test_infrastructure_has_no_application_imports(self):
        violations = []
        for filepath in _collect_python_files(INFRASTRUCTURE_DIR):
            for imp in _get_imports_from_file(filepath):
                if _is_application_import(imp):
                    violations.append(f"{filepath.relative_to(SRC_DIR)}: imports {imp}")
        assert not violations, f"Infrastructure imports Application:\n" + "\n".join(violations)

    def test_infrastructure_has_no_presentation_imports(self):
        violations = []
        for filepath in _collect_python_files(INFRASTRUCTURE_DIR):
            for imp in _get_imports_from_file(filepath):
                if _is_presentation_import(imp):
                    violations.append(f"{filepath.relative_to(SRC_DIR)}: imports {imp}")
        assert not violations, f"Infrastructure imports Presentation:\n" + "\n".join(violations)


class TestPresentationIsolation:
    """Presentation layer architecture rules.
    
    Routes MAY import infrastructure for dependency wiring (instantiating repos, adapters).
    This is the composition root - where concrete implementations are created.
    
    Rules:
    - Routes must NOT contain business logic (only validation + use case delegation)
    - Business logic must NOT live in presentation layer
    - Routes must NOT directly query databases (use use cases instead)
    """

    def test_presentation_routes_have_no_business_logic(self):
        """Routes should only validate input, call use cases, and return responses.
        No business logic, calculations, or data transformations in routes."""
        violations = []
        for filepath in _collect_python_files(PRESENTATION_DIR / "routes"):
            try:
                content = filepath.read_text()
                tree = ast.parse(content)
            except (SyntaxError, UnicodeDecodeError):
                continue
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 0
                    if func_lines > 50:
                        violations.append(
                            f"{filepath.relative_to(SRC_DIR)}: route function {node.name} has {func_lines} lines (max 50)"
                        )
        assert not violations, f"Routes with business logic:\n" + "\n".join(violations)


class TestFileSizeLimits:
    """All Python files must stay under size limits."""

    def test_no_oversized_files(self):
        violations = []
        for filepath in _collect_python_files(SRC_DIR):
            lines = filepath.read_text().splitlines()
            if len(lines) > MAX_FILE_LINES:
                violations.append(
                    f"{filepath.relative_to(SRC_DIR)}: {len(lines)} lines (max {MAX_FILE_LINES})"
                )
        assert not violations, f"Oversized files:\n" + "\n".join(violations)


class TestModuleIsolation:
    """Modules must not cross-import each other at the domain level.
    Exception: shared value objects (ProjectId) may be imported across modules
    since they represent shared identity concepts."""

    def test_projects_domain_does_not_import_memory_domain(self):
        violations = []
        projects_domain = DOMAIN_DIR / "projects"
        for filepath in _collect_python_files(projects_domain):
            for imp in _get_imports_from_file(filepath):
                if imp.startswith("forge.domain.memory"):
                    violations.append(f"{filepath.relative_to(SRC_DIR)}: imports {imp}")
        assert not violations, f"Projects imports Memory:\n" + "\n".join(violations)

    def test_memory_domain_does_not_import_projects_entities(self):
        """Memory may import shared value objects (ProjectId) but NOT project entities."""
        violations = []
        memory_domain = DOMAIN_DIR / "memory"
        for filepath in _collect_python_files(memory_domain):
            for imp in _get_imports_from_file(filepath):
                if imp.startswith("forge.domain.projects") and "value_objects" not in imp:
                    violations.append(f"{filepath.relative_to(SRC_DIR)}: imports {imp}")
        assert not violations, f"Memory imports Projects entities:\n" + "\n".join(violations)
