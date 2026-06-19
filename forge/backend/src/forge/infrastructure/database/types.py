"""Database types that work across SQLite and PostgreSQL."""
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


def UUIDType():
    """Return a UUID column type that works with both SQLite and PostgreSQL."""
    from forge.config.settings import get_settings
    settings = get_settings()
    if "sqlite" in settings.DATABASE_URL:
        return String(36)
    return PG_UUID(as_uuid=True)
