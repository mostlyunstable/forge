"""Dependency schemas."""

from pydantic import BaseModel, Field


class DependencyBase(BaseModel):
    source_file: str
    target_file: str
    dependency_type: str
    line_number: int


class DependencyResponse(DependencyBase):
    source_name: str
    target_name: str


class ImportNodeResponse(BaseModel):
    file_path: str
    imports: list[str] = []
    line_numbers: list[int] = []


class BuildDependencyGraphRequest(BaseModel):
    project_id: str
    indexed_files: list[dict] = Field(default_factory=list)


class BuildDependencyGraphResponse(BaseModel):
    total_files: int
    total_dependencies: int
    files_with_imports: int
    files_imported: int
    cycles: list[list[str]] = []


class GetImportGraphResponse(BaseModel):
    file_path: str
    direct_imports: list[ImportNodeResponse] = []
    transitive_imports: list[ImportNodeResponse] = []
    imported_by: list[ImportNodeResponse] = []


class CallNodeResponse(BaseModel):
    file_path: str
    entry_name: str
    line_number: int


class GetCallGraphResponse(BaseModel):
    entry_name: str
    calls: list[CallNodeResponse] = []
    called_by: list[CallNodeResponse] = []
