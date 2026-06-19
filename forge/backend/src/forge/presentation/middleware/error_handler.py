"""Global error handler middleware."""
from __future__ import annotations

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

from forge.domain.projects.exceptions import ProjectNotFoundError, ProjectAlreadyExistsError
from forge.domain.memory.exceptions import DecisionNotFoundError, BugNotFoundError, PreferenceNotFoundError
from forge.domain.code.exceptions import CodeEntryNotFoundError, IndexingError
from forge.domain.git.exceptions import CommitNotFoundError

logger = structlog.get_logger()


class ErrorCode:
    """Machine-readable error codes for API responses."""

    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    PROJECT_ALREADY_EXISTS = "PROJECT_ALREADY_EXISTS"
    DECISION_NOT_FOUND = "DECISION_NOT_FOUND"
    BUG_NOT_FOUND = "BUG_NOT_FOUND"
    PREFERENCE_NOT_FOUND = "PREFERENCE_NOT_FOUND"
    CODE_ENTRY_NOT_FOUND = "CODE_ENTRY_NOT_FOUND"
    INDEXING_ERROR = "INDEXING_ERROR"
    COMMIT_NOT_FOUND = "COMMIT_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    UNAUTHORIZED = "UNAUTHORIZED"
    ANALYSIS_REPORT_NOT_FOUND = "ANALYSIS_REPORT_NOT_FOUND"
    ANALYSIS_ERROR = "ANALYSIS_ERROR"


def _error_response(status_code: int, error_code: str, detail: str) -> JSONResponse:
    """Create a structured error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error_code": error_code,
            "detail": detail,
        },
    )


async def project_not_found_handler(request: Request, exc: ProjectNotFoundError) -> JSONResponse:
    return _error_response(404, ErrorCode.PROJECT_NOT_FOUND, str(exc))


async def project_already_exists_handler(request: Request, exc: ProjectAlreadyExistsError) -> JSONResponse:
    return _error_response(409, ErrorCode.PROJECT_ALREADY_EXISTS, str(exc))


async def decision_not_found_handler(request: Request, exc: DecisionNotFoundError) -> JSONResponse:
    return _error_response(404, ErrorCode.DECISION_NOT_FOUND, str(exc))


async def bug_not_found_handler(request: Request, exc: BugNotFoundError) -> JSONResponse:
    return _error_response(404, ErrorCode.BUG_NOT_FOUND, str(exc))


async def preference_not_found_handler(request: Request, exc: PreferenceNotFoundError) -> JSONResponse:
    return _error_response(404, ErrorCode.PREFERENCE_NOT_FOUND, str(exc))


async def code_entry_not_found_handler(request: Request, exc: CodeEntryNotFoundError) -> JSONResponse:
    return _error_response(404, ErrorCode.CODE_ENTRY_NOT_FOUND, str(exc))


async def indexing_error_handler(request: Request, exc: IndexingError) -> JSONResponse:
    return _error_response(422, ErrorCode.INDEXING_ERROR, str(exc))


async def commit_not_found_handler(request: Request, exc: CommitNotFoundError) -> JSONResponse:
    return _error_response(404, ErrorCode.COMMIT_NOT_FOUND, str(exc))


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", error=str(exc), exc_info=True)
    return _error_response(500, ErrorCode.INTERNAL_ERROR, "Internal server error")
