from enum import Enum

class ConversationState(Enum):
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    SUMMARIZED = "SUMMARIZED"
    ARCHIVED = "ARCHIVED"
