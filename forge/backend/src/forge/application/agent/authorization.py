from typing import Any, List

class ToolAuthorizationPolicy:
    """
    Independently validates every tool request from the LLM.
    Provides defense-in-depth against prompt injection and unauthorized execution.
    """
    
    @classmethod
    def authorize(cls, tool_name: str, arguments: dict[str, Any], allowed_tools: List[str] | None = None) -> None:
        """
        Validates if the tool execution is authorized for the current context.
        Raises PermissionError if unauthorized.
        """
        # If allowed_tools is specified, enforce it strictly.
        if allowed_tools is not None:
            if tool_name not in allowed_tools:
                raise PermissionError(f"UNAUTHORIZED ACTION: Tool '{tool_name}' is not allowed in this context.")

        # Additional domain-specific tool constraints could go here.
        # e.g., if we want to globally disable 'run_python_code' in certain environments.
        pass
