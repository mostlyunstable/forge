from dataclasses import dataclass


@dataclass
class AgentProfile:
    name: str
    role: str
    system_prompt_template: str
    allowed_tools: list[str]
