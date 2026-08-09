"""Domain exceptions for the Conversation module."""


class ConversationNotFoundError(Exception):
    """Raised when a conversation cannot be found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(f"Conversation not found: {identifier}")
        self.identifier = identifier


class ConversationAccessDeniedError(Exception):
    """Raised when a user tries to access a conversation they don't own."""

    def __init__(self, conversation_id: str) -> None:
        super().__init__(f"Access denied to conversation: {conversation_id}")
        self.conversation_id = conversation_id


class ConversationLimitExceededError(Exception):
    """Raised when too many conversations exist for a project."""

    def __init__(self, project_id: str, limit: int) -> None:
        super().__init__(f"Conversation limit ({limit}) exceeded for project: {project_id}")
        self.project_id = project_id
        self.limit = limit
