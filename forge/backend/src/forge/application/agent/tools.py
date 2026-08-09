import json
import os
import subprocess
from pathlib import Path
from typing import Any

import threading

_thread_local = threading.local()
_ALLOWED_BASE_DIR: Path | None = None


def set_tools_base_dir(base_dir: str | Path) -> None:
    """Set the allowed base directory for file operations."""
    global _ALLOWED_BASE_DIR  # noqa: PLW0603
    path = Path(base_dir).resolve()
    _ALLOWED_BASE_DIR = path
    _thread_local.base_dir = path


def get_tools_base_dir() -> Path | None:
    """Get base dir: thread-local if set, else global fallback."""
    return getattr(_thread_local, 'base_dir', _ALLOWED_BASE_DIR)


def _safe_path(filepath: str) -> Path:
    """Resolve filepath and ensure it's within the allowed base directory.

    Raises:
        PermissionError: If the path escapes the sandbox.
    """
    base_dir = get_tools_base_dir()
    if base_dir is None:
        raise PermissionError(
            "File operations are disabled: no project directory has been set."
        )
    resolved = Path(filepath).resolve()
    try:
        resolved.relative_to(base_dir)
    except ValueError:
        raise PermissionError(
            f"Access denied: path '{filepath}' is outside the project directory."
        )
    return resolved





class ForgeTools:
    @staticmethod
    def get_tool_schemas() -> list[dict[str, Any]]:
        """Return the JSON schemas for the tools to pass to the LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "delegate_task",
                    "description": "Delegates a complex sub-task to a specialized agent (e.g., 'code_debugger', 'researcher'). The agent will execute the task and return a summary of its findings and actions. The current context window is NOT passed to the child agent, so you must explain the task completely.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_name": {
                                "type": "string",
                                "description": "The name of the agent to delegate to.",
                            },
                            "task": {
                                "type": "string",
                                "description": "A detailed explanation of what the agent should accomplish.",
                            }
                        },
                        "required": ["agent_name", "task"],
                    },
                },
            },
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
                import shlex

                command = arguments["command"]

                ALLOWED_EXECUTABLES = {"rg", "grep", "find", "ls", "cat", "git", "echo", "pwd", "wc", "head", "tail", "sort", "uniq", "diff", "python3", "python", "uv", "pytest"}

                try:
                    tokens = shlex.split(command)
                except ValueError as e:
                    return f"Error parsing command: {e}"

                if not tokens:
                    return "Error: Empty command"

                executable = os.path.basename(tokens[0])
                if executable not in ALLOWED_EXECUTABLES:
                    return f"Error: Executable '{executable}' is not allowed."

                base_dir = get_tools_base_dir()
                cwd = str(base_dir) if base_dir else None
                result = subprocess.run(
                    tokens,
                    shell=False,
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

                if len(output) > 50000:
                    output = output[:50000] + "\n... (output truncated)"
                return output

            elif name == "learn_rule":
                rule = arguments["rule"]
                # Rules are project-scoped — write to the current project directory, not the Forge system directory
                base_dir = get_tools_base_dir()
                if base_dir is None:
                    return "Error: Cannot learn rules — no project directory is set."
                rules_path = base_dir / ".forge_rules.md"
                existing = ""
                if rules_path.exists():
                    existing = rules_path.read_text(encoding="utf-8")
                new_content = existing + f"\n- {rule}" if existing else f"- {rule}"
                rules_path.write_text(new_content, encoding="utf-8")
                return f"Successfully learned rule for this project: {rule}"

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

                    if len(output) > 50000:
                        output = output[:50000] + "\n... (output truncated)"
                    return output
                finally:
                    os.unlink(temp_file_name)

            else:
                return f"Error: Unknown tool {name}"

        except Exception as e:
            return f"Error executing tool {name}: {str(e)}"
