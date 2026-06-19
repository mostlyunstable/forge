"""Code schemas."""
from pydantic import BaseModel, Field, field_validator

from forge.presentation.schemas.validators import validate_uuid


class IndexRepositoryRequest(BaseModel):
    project_id: str
    repo_path: str = Field(..., min_length=1)

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        return validate_uuid(v)


class IndexRepositoryResponse(BaseModel):
    files_indexed: int
    entries_found: int
    entry_types: dict[str, int]


class CodeEntryResultResponse(BaseModel):
    id: str
    name: str
    entry_type: str
    file_path: str
    language: str
    start_line: int
    end_line: int


class SearchCodeResponse(BaseModel):
    results: list[CodeEntryResultResponse]
    query: str
    total: int


class FileEntryDetailResponse(BaseModel):
    name: str
    entry_type: str
    content: str
    language: str
    start_line: int
    end_line: int
    metadata: dict


class GetFileEntriesResponse(BaseModel):
    file_path: str
    entries: list[FileEntryDetailResponse]
    total: int
