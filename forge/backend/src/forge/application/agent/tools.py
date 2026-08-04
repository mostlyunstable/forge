import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

# Sandbox: all file operations must resolve within this directory
_ALLOWED_BASE_DIR: Path | None = None

# Commands that should never be executed via the agent shell tool
_BLOCKED_COMMAND_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\brm\s+-rf\s+/"),      # rm -rf /
    re.compile(r"\bmkfs\b"),             # filesystem format
    re.compile(r"\bdd\s+if="),           # raw disk write
    re.compile(r"\b:()\s*\{"),           # fork bomb
    re.compile(r"\bcurl\b.*\|\s*bash"),  # pipe-to-shell
    re.compile(r"\bwget\b.*\|\s*bash"),
    re.compile(r"\bchmod\s+777\s+/"),    # global permission change
    re.compile(r"\bsudo\b"),             # privilege escalation
]


def set_tools_base_dir(base_dir: str | Path) -> None:
    """Set the allowed base directory for file operations."""
    global _ALLOWED_BASE_DIR  # noqa: PLW0603
    _ALLOWED_BASE_DIR = Path(base_dir).resolve()


def _safe_path(filepath: str) -> Path:
    """Resolve filepath and ensure it's within the allowed base directory.

    Raises:
        PermissionError: If the path escapes the sandbox.
    """
    if _ALLOWED_BASE_DIR is None:
        raise PermissionError(
            "File operations are disabled: no project directory has been set."
        )
    resolved = Path(filepath).resolve()
    if not str(resolved).startswith(str(_ALLOWED_BASE_DIR)):
        raise PermissionError(
            f"Access denied: path '{filepath}' is outside the project directory."
        )
    return resolved


def _check_command_safety(command: str) -> str | None:
    """Return an error message if the command matches a blocked pattern."""
    for pattern in _BLOCKED_COMMAND_PATTERNS:
        if pattern.search(command):
            return f"Blocked: command matches dangerous pattern '{pattern.pattern}'."
    return None


class ForgeTools:
    @staticmethod
    def get_tool_schemas() -> list[dict[str, Any]]:
        """Return the JSON schemas for the tools to pass to the LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Reads the content of a file from the local filesystem.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "The absolute or relative path to the file to read.",
                            }
                        },
                        "required": ["filepath"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Writes content to a file, overwriting if it exists, or creating it if it doesn't.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "The path to the file to write to.",
                            },
                            "content": {
                                "type": "string",
                                "description": "The text content to write into the file.",
                            },
                        },
                        "required": ["filepath", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_shell_command",
                    "description": "Executes a shell command in the terminal and returns the standard output and error. Use this to search code (grep/rg), list directories (ls), check tests, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The bash shell command to execute.",
                            }
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "learn_rule",
                    "description": "Appends a new permanent rule or preference to the .forge_rules.md file. Use this when the user corrects you or asks you to remember a specific convention or behavior for all future conversations.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "rule": {
                                "type": "string",
                                "description": "The rule or preference to remember. Should be clear and actionable.",
                            }
                        },
                        "required": ["rule"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Searches the web for a query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query."}
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_python_code",
                    "description": "Executes a string of Python code and returns output.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "The Python code to execute."}
                        },
                        "required": ["code"],
                    },
                },
            },
        ]

    @staticmethod
    def execute_tool(name: str, arguments: dict[str, Any]) -> str:
        """Executes a tool by name and returns its string result."""
        try:
            if name == "read_file":
                filepath = arguments["filepath"]
                safe = _safe_path(filepath)
                if not safe.exists():
                    return f"Error: File not found: {filepath}"
                return safe.read_text(encoding="utf-8")

            elif name == "write_file":
                filepath = arguments["filepath"]
                content = arguments["content"]
                safe = _safe_path(filepath)
                safe.parent.mkdir(parents=True, exist_ok=True)
                safe.write_text(content, encoding="utf-8")
                return f"Successfully wrote to {filepath}"

            elif name == "run_shell_command":
                command = arguments["command"]
                # Check against denylist before execution
                blocked = _check_command_safety(command)
                if blocked:
                    return f"Error: {blocked}"
                cwd = str(_ALLOWED_BASE_DIR) if _ALLOWED_BASE_DIR else None
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30.0,
                    cwd=cwd,
                )
                output = result.stdout
                if result.stderr:
                    output += "\nSTDERR:\n" + result.stderr
                if not output.strip():
                    return "Command executed successfully with no output."
                return output

            elif name == "learn_rule":
                rule = arguments["rule"]
                backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
                forge_dir = backend_dir.parent
                rules_path = forge_dir / ".forge_rules.md"

                existing = ""
                if rules_path.exists():
                    existing = rules_path.read_text(encoding="utf-8")

                new_content = existing + f"\n- {rule}" if existing else f"- {rule}"
                rules_path.write_text(new_content, encoding="utf-8")
                return f"Successfully learned rule: {rule}"

            elif name == "search_web":
                from ddgs import DDGS

                query = arguments["query"]
                results = list(DDGS().text(query, max_results=5))
                return json.dumps(results)

            elif name == "run_python_code":
                import tempfile

                code = arguments["code"]
                with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                    f.write(code)
                    temp_file_name = f.name

                try:
                    import sys

                    result = subprocess.run(
                        [sys.executable, temp_file_name],
                        capture_output=True,
                        text=True,
                        timeout=30.0,
                    )
                    output = result.stdout
                    if result.stderr:
                        output += "\nSTDERR:\n" + result.stderr
                    if not output.strip():
                        return "Command executed successfully with no output."
                    return output
                finally:
                    os.unlink(temp_file_name)

            else:
                return f"Error: Unknown tool {name}"

        except Exception as e:
            return f"Error executing tool {name}: {str(e)}"
