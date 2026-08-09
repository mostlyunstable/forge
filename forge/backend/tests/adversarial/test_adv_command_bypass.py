import os
import pytest
import subprocess
from pathlib import Path

from forge.application.agent.tools import (
    set_tools_base_dir,
    ForgeTools,
)

@pytest.fixture
def command_env(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    # Write a sensitive file outside
    (tmp_path / "sensitive.txt").write_text("I am sensitive data")
    
    yield project_dir, tmp_path

@pytest.mark.parametrize("payload", [
    # Bypassing using absolute paths of allowed binaries
    "/bin/cat ../sensitive.txt",
    "/usr/bin/find / -name '*secret*'",
    
    # Path traversal with allowed binaries
    "cat ../sensitive.txt",
    "grep 'secret' ../sensitive.txt",
    "cat /etc/passwd",
    
    # Command injection attempts
    "cat safe.txt; ls -la /",
    "cat safe.txt && cat /etc/passwd",
    "cat safe.txt | head",
    "git config --global core.editor 'cat /etc/passwd'",
    "python3 -c \"import os; print(os.listdir('/'))\"",
])
def test_adversarial_command_bypass(command_env, payload):
    project_dir, tmp_path = command_env
    set_tools_base_dir(project_dir)
    
    # The sandbox allowed list checks the first token. We want to test if it protects against
    # path traversal in the arguments.
    result = ForgeTools.execute_tool("run_shell_command", {"command": payload})
    
    # The allowlist only checks the executable name. If `cat ../sensitive.txt` succeeds,
    # then the executable is allowed, but the argument authorization is completely missing.
    assert "sensitive data" not in result, f"Command execution bypass succeeded. Payload '{payload}' leaked data: {result}"
    assert "root:" not in result, f"Command execution bypass succeeded. Payload '{payload}' leaked /etc/passwd: {result}"
