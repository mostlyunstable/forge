"""Conversation schemas."""

from pydantic import BaseModel, Field, field_validator

from forge.presentation.schemas.validators import validate_uuid


class CreateConversationRequest(BaseModel):
    project_id: str
    title: str = Field(..., min_length=1, max_length=255)

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        return validate_uuid(v)


class ConversationSummaryResponse(BaseModel):
    id: str
    project_id: str
    title: str
    summary: str
    message_count: int
    total_token_count: int
    created_at: str
    updated_at: str


class ListConversationsResponse(BaseModel):
    conversations: list[ConversationSummaryResponse]
    total: int


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    token_count: int
    created_at: str


class ConversationHistoryResponse(BaseModel):
    id: str
    project_id: str
    title: str
    summary: str
    messages: list[MessageResponse]
    message_count: int
    total_token_count: int
    created_at: str
    updated_at: str


class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatSourceResponse(BaseModel):
    type: str
    name: str
    score: float
    file: str | None = None


class SendMessageResponse(BaseModel):
    message_id: str
    conversation_id: str
    response: str
    sources: list[ChatSourceResponse]
    token_count: int
    message_count: int


class RenameConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class RenameConversationResponse(BaseModel):
    id: str
    title: str
    updated_at: str


class DeleteConversationResponse(BaseModel):
    deleted: bool
    conversation_id: str


class SearchConversationsResponse(BaseModel):
    conversations: list[ConversationSummaryResponse]
    total: int
    query: str


class SummarizeConversationResponse(BaseModel):
    conversation_id: str
    summary: str
    message_count_pruned: int
