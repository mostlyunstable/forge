"""Application settings loaded from environment."""

from __future__ import annotations

import warnings
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration. All values come from environment variables."""

    APP_NAME: str = "Forge"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite+aiosqlite:///./forge.db"
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    USE_QDRANT: bool = False

    JWT_SECRET_KEY: str = "change-me-in-production-must-be-32-bytes"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30

    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = {"env_file": ".env", "case_sensitive": True}

    def validate_production(self) -> None:
        """Validate settings for production readiness. Call at startup.

        Raises:
            RuntimeError: If critical production settings are missing.
        """
        # Always enforce minimum key length, even in debug mode
        if len(self.JWT_SECRET_KEY) < 32:
            raise RuntimeError(
                "JWT_SECRET_KEY must be at least 32 bytes. "
                "Set the JWT_SECRET_KEY environment variable."
            )
        # In production, also reject the default placeholder key
        if not self.DEBUG and self.JWT_SECRET_KEY == "change-me-in-production-must-be-32-bytes":
            raise RuntimeError(
                "JWT_SECRET_KEY must be set to a secure value in production. "
                "Set the JWT_SECRET_KEY environment variable."
            )
        if not self.LLM_API_KEY:
            warnings.warn(
                "LLM_API_KEY is empty - LLM features will fail.", UserWarning, stacklevel=2
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
