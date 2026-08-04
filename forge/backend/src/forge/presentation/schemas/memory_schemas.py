"""Memory schemas."""

from pydantic import BaseModel, Field, field_validator

from forge.presentation.schemas.validators import validate_severity, validate_uuid


class SaveDecisionRequest(BaseModel):
    project_id: str
    title: str = Field(..., min_length=1, max_length=255)
    decision: str = Field(..., min_length=1)
    reason: str = ""
    alternatives: list[str] = Field(default_factory=list)

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        return validate_uuid(v)


class UpdateDecisionRequest(BaseModel):
    title: str | None = None
    decision: str | None = None
    reason: str | None = None
    alternatives: list[str] | None = None
    status: str | None = None


class DecisionResponse(BaseModel):
    id: str
    project_id: str
    title: str
    decision: str
    reason: str
    alternatives: list[str]
    status: str
    created_at: str


class DecisionSummaryResponse(BaseModel):
    id: str
    title: str
    decision: str
    status: str
    created_at: str


class ListDecisionsResponse(BaseModel):
    decisions: list[DecisionSummaryResponse]
    total: int
    project_id: str


class SaveBugRequest(BaseModel):
    project_id: str
    title: str = Field(..., min_length=1, max_length=255)
    problem: str = Field(..., min_length=1)
    root_cause: str = ""
    solution: str = ""
    affected_files: list[str] = Field(default_factory=list)
    severity: str = "medium"

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        return validate_uuid(v)

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        return validate_severity(v)


class UpdateBugRequest(BaseModel):
    title: str | None = None
    problem: str | None = None
    root_cause: str | None = None
    solution: str | None = None
    affected_files: list[str] | None = None
    severity: str | None = None
    resolved: bool | None = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_severity(v)


class BugResponse(BaseModel):
    id: str
    project_id: str
    title: str
    problem: str
    root_cause: str
    solution: str
    affected_files: list[str]
    severity: str
    resolved: bool
    created_at: str


class BugSummaryResponse(BaseModel):
    id: str
    title: str
    severity: str
    resolved: bool
    created_at: str


class ListBugsResponse(BaseModel):
    bugs: list[BugSummaryResponse]
    total: int
    project_id: str


class SavePreferenceRequest(BaseModel):
    key: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class PreferenceResponse(BaseModel):
    key: str
    value: str
    confidence: float
    evidence_count: int
    created_at: str
    updated_at: str


class MemoryResultResponse(BaseModel):
    type: str
    id: str
    title: str
    content: str
    score: float


class SearchMemoriesResponse(BaseModel):
    results: list[MemoryResultResponse]
    query: str
    total: int


class GetPreferencesResponse(BaseModel):
    preferences: list[PreferenceResponse]
    total: int


class DeleteResponse(BaseModel):
    deleted: bool
    id: str
