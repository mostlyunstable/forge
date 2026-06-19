"""Project schemas."""
from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    stack: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    repository_url: str | None = None


class UpdateProjectRequest(BaseModel):
    description: str | None = None
    stack: list[str] | None = None
    goals: list[str] | None = None
    repository_url: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    stack: list[str]
    goals: list[str]
    status: str
    repository_url: str | None = None
    created_at: str
    updated_at: str


class ProjectSummaryResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str
    stack: list[str]


class ListProjectsResponse(BaseModel):
    projects: list[ProjectSummaryResponse]
    total: int


class DeleteResponse(BaseModel):
    deleted: bool
    project_id: str
