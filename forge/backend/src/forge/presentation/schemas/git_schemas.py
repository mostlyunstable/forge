"""Git schemas."""
from pydantic import BaseModel


class CommitSummaryResponse(BaseModel):
    sha: str
    message: str
    author: str
    classification: str
    files_changed: list[str]
    timestamp: str


class AnalyzeCommitsResponse(BaseModel):
    commits: list[CommitSummaryResponse]
    total: int
    by_classification: dict[str, int]
