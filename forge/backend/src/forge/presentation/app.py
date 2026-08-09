"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
import os
import secrets
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from forge.config.logging import setup_logging
from forge.config.metrics import APP_INFO
from forge.config.settings import get_settings
from forge.domain.analysis.exceptions import AnalysisError, AnalysisReportNotFoundError
from forge.domain.code.exceptions import CodeEntryNotFoundError, IndexingError
from forge.domain.conversation.exceptions import (
    ConversationAccessDeniedError,
    ConversationLimitExceededError,
    ConversationNotFoundError,
)
from forge.domain.git.exceptions import CommitNotFoundError
from forge.domain.memory.exceptions import (
    BugNotFoundError,
    DecisionNotFoundError,
    PreferenceNotFoundError,
)
from forge.domain.projects.exceptions import ProjectAlreadyExistsError, ProjectNotFoundError
from forge.infrastructure.database.connection import database_manager
from forge.infrastructure.search.in_memory_vector_store import in_memory_vector_store
from forge.infrastructure.search.qdrant_client import vector_store
from forge.presentation.deps import verify_auth_token
from forge.presentation.middleware.error_handler import (
    ErrorCode,
    _error_response,
    bug_not_found_handler,
    code_entry_not_found_handler,
    commit_not_found_handler,
    conversation_access_denied_handler,
    conversation_limit_exceeded_handler,
    conversation_not_found_handler,
    decision_not_found_handler,
    generic_error_handler,
    indexing_error_handler,
    preference_not_found_handler,
    project_already_exists_handler,
    project_not_found_handler,
)
from forge.presentation.middleware.metrics import MetricsMiddleware
from forge.presentation.middleware.rate_limit import RateLimitMiddleware
from forge.presentation.middleware.request_id import RequestIDMiddleware
from forge.presentation.routes import (
    analysis,
    chat,
    code,
    conversations,
    dependencies,
    git,
    index,
    memory,
    metrics,
    projects,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    token_file_created = False
    if not os.environ.get("FORGE_API_KEY"):
        token = secrets.token_hex(32)
        os.environ["FORGE_API_KEY"] = token
        with open(".forge_auth_token", "w") as f:
            f.write(token)
        token_file_created = True

    setup_logging(log_level="INFO", json_output=True)
    settings = get_settings()
    settings.validate_production()
    APP_INFO.info({"version": settings.APP_VERSION, "name": settings.APP_NAME})
    logger.info("application_starting", version=settings.APP_VERSION)
    await database_manager.run_migrations()
    
    # Recover orphaned running index jobs
    try:
        from sqlalchemy import update
        from forge.infrastructure.database.models.index_job_model import IndexJobModel
        from forge.domain.indexing.value_objects.job_status import JobStatus
        
        async with database_manager.get_session() as session:
            await session.execute(
                update(IndexJobModel)
                .where(IndexJobModel.status == JobStatus.RUNNING.value)
                .values(
                    status=JobStatus.FAILED.value,
                    error_log=["System crashed or was restarted while the job was running."]
                )
            )
            await session.commit()
        logger.info("startup_recovery_completed")
    except Exception as e:
        logger.error("startup_recovery_failed", error=str(e))

    if settings.USE_QDRANT:
        await vector_store.init_collections()
    else:
        await in_memory_vector_store.init_collections()
    logger.info("application_ready")
    yield
    logger.info("application_shutting_down")
    await database_manager.close()
    
    if token_file_created and os.path.exists(".forge_auth_token"):
        try:
            os.remove(".forge_auth_token")
        except OSError:
            pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(MetricsMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)

    app.add_exception_handler(ProjectNotFoundError, project_not_found_handler)
    app.add_exception_handler(ProjectAlreadyExistsError, project_already_exists_handler)
    app.add_exception_handler(DecisionNotFoundError, decision_not_found_handler)
    app.add_exception_handler(BugNotFoundError, bug_not_found_handler)
    app.add_exception_handler(PreferenceNotFoundError, preference_not_found_handler)
    app.add_exception_handler(CodeEntryNotFoundError, code_entry_not_found_handler)
    app.add_exception_handler(IndexingError, indexing_error_handler)
    app.add_exception_handler(CommitNotFoundError, commit_not_found_handler)
    app.add_exception_handler(
        AnalysisReportNotFoundError,
        lambda req, exc: _error_response(404, ErrorCode.ANALYSIS_REPORT_NOT_FOUND, str(exc)),
    )
    app.add_exception_handler(
        AnalysisError,
        lambda req, exc: _error_response(422, ErrorCode.ANALYSIS_ERROR, str(exc)),
    )
    app.add_exception_handler(
        ConversationNotFoundError,
        conversation_not_found_handler,
    )
    app.add_exception_handler(
        ConversationAccessDeniedError,
        conversation_access_denied_handler,
    )
    app.add_exception_handler(
        ConversationLimitExceededError,
        conversation_limit_exceeded_handler,
    )
    app.add_exception_handler(Exception, generic_error_handler)

    deps = [Depends(verify_auth_token)]

    app.include_router(projects.router, prefix="/api/v1", )
    app.include_router(memory.router, prefix="/api/v1", )
    app.include_router(chat.router, prefix="/api/v1", )
    app.include_router(code.router, prefix="/api/v1", )
    app.include_router(git.router, prefix="/api/v1", )
    app.include_router(dependencies.router, prefix="/api/v1", )
    app.include_router(analysis.router, prefix="/api/v1", )
    app.include_router(index.router, prefix="/api/v1", )
    app.include_router(conversations.router, prefix="/api/v1", )
    app.include_router(metrics.router, )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
