"""Chat schemas."""

from pydantic import BaseModel, Field, field_validator

from forge.presentation.schemas.validators import validate_uuid


class SendMessageRequest(BaseModel):
    project_id: str
    message: str = Field(..., min_length=1)

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        return validate_uuid(v)


class ChatSourceResponse(BaseModel):
    type: str
    name: str
    score: float
    file: str | None = None


class SendMessageResponse(BaseModel):
    response: str
    sources: list[ChatSourceResponse]
    project_id: str
