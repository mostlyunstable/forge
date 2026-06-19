"""Shared Pydantic validators."""
from pydantic import field_validator


def validate_uuid(value: str) -> str:
    """Validate that a string is a valid UUID."""
    import uuid
    try:
        uuid.UUID(value)
    except ValueError:
        raise ValueError(f"Invalid UUID format: {value}")
    return value


def validate_severity(value: str) -> str:
    """Validate bug severity level."""
    valid_severities = {"low", "medium", "high", "critical"}
    if value.lower() not in valid_severities:
        raise ValueError(f"Severity must be one of: {', '.join(sorted(valid_severities))}")
    return value.lower()


def validate_project_status(value: str) -> str:
    """Validate project status."""
    valid_statuses = {"active", "archived", "deleted"}
    if value.lower() not in valid_statuses:
        raise ValueError(f"Status must be one of: {', '.join(sorted(valid_statuses))}")
    return value.lower()


def validate_decision_status(value: str) -> str:
    """Validate decision status."""
    valid_statuses = {"accepted", "rejected", "superseded", "deprecated"}
    if value.lower() not in valid_statuses:
        raise ValueError(f"Status must be one of: {', '.join(sorted(valid_statuses))}")
    return value.lower()
