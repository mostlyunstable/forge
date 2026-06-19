"""Middleware tests."""
import pytest
from forge.presentation.middleware.auth import create_access_token, verify_token
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


class TestJWTAuth:
    def test_create_access_token(self):
        token = create_access_token({"sub": "test-user"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        token = create_access_token({"sub": "test-user"})
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        result = verify_token(creds)
        assert result["sub"] == "test-user"

    def test_verify_missing_credentials(self):
        with pytest.raises(HTTPException) as exc_info:
            verify_token(None)
        assert exc_info.value.status_code == 401

    def test_verify_invalid_token(self):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
        with pytest.raises(HTTPException) as exc_info:
            verify_token(creds)
        assert exc_info.value.status_code == 401


class TestErrorCodes:
    def test_error_code_constants(self):
        from forge.presentation.middleware.error_handler import ErrorCode
        assert ErrorCode.PROJECT_NOT_FOUND == "PROJECT_NOT_FOUND"
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"


class TestRequestValidation:
    def test_severity_validator_valid(self):
        from forge.presentation.schemas.validators import validate_severity
        assert validate_severity("low") == "low"
        assert validate_severity("HIGH") == "high"
        assert validate_severity("Critical") == "critical"

    def test_severity_validator_invalid(self):
        from forge.presentation.schemas.validators import validate_severity
        with pytest.raises(ValueError):
            validate_severity("invalid")

    def test_uuid_validator_valid(self):
        from forge.presentation.schemas.validators import validate_uuid
        result = validate_uuid("12345678-1234-1234-1234-123456789012")
        assert result == "12345678-1234-1234-1234-123456789012"

    def test_uuid_validator_invalid(self):
        from forge.presentation.schemas.validators import validate_uuid
        with pytest.raises(ValueError):
            validate_uuid("not-a-uuid")

    def test_project_status_validator(self):
        from forge.presentation.schemas.validators import validate_project_status
        assert validate_project_status("active") == "active"
        assert validate_project_status("ARCHIVED") == "archived"
        with pytest.raises(ValueError):
            validate_project_status("invalid")
