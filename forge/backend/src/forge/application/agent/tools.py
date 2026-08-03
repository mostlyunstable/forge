import os
import subprocess
import json
from typing import Any

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
                                "description": "The absolute or relative path to the file to read."
                            }
                        },
                        "required": ["filepath"]
                    }
                }
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
                                "description": "The path to the file to write to."
                            },
                            "content": {
                                "type": "string",
                                "description": "The text content to write into the file."
                            }
                        },
                        "required": ["filepath", "content"]
                    }
                }
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
                                "description": "The bash shell command to execute."
                            }
                        },
                        "required": ["command"]
                    }
                }
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
                                "description": "The rule or preference to remember. Should be clear and actionable."
                            }
                        },
                        "required": ["rule"]
                    }
                }
            }
        ]

    @staticmethod
    def execute_tool(name: str, arguments: dict[str, Any]) -> str:
        """Executes a tool by name and returns its string result."""
        from pathlib import Path
        try:
            if name == "read_file":
                filepath = arguments["filepath"]
                if not os.path.exists(filepath):
                    return f"Error: File not found: {filepath}"
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                return content
                
            elif name == "write_file":
                filepath = arguments["filepath"]
                content = arguments["content"]
                os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Successfully wrote to {filepath}"
                
            elif name == "run_shell_command":
                command = arguments["command"]
                # Execute command with shell=True for standard shell features like pipes
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30.0  # Prevents hanging commands
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
                
            else:
                return f"Error: Unknown tool {name}"
                
        except Exception as e:
            return f"Error executing tool {name}: {str(e)}"
