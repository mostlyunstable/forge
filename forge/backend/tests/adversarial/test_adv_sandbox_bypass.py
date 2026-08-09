import os
import pytest
import shutil
from pathlib import Path

from forge.application.agent.tools import (
    set_tools_base_dir,
    ForgeTools,
)

@pytest.fixture
def sandbox_env(tmp_path):
    project_dir = tmp_path / "project"
    evil_dir = tmp_path / "project-evil"
    outside_dir = tmp_path / "outside"
    
    project_dir.mkdir()
    evil_dir.mkdir()
    outside_dir.mkdir()
    
    (project_dir / "safe.txt").write_text("safe")
    (evil_dir / "evil.txt").write_text("evil")
    (outside_dir / "outside.txt").write_text("outside")
    (outside_dir / "secret.key").write_text("super_secret")
    
    # Create symlinks inside project
    os.symlink(str(outside_dir), str(project_dir / "symlink_outside"))
    
    yield project_dir, tmp_path
    
@pytest.mark.parametrize("payload", [
    "../outside/outside.txt",
    "../../outside/outside.txt",
    "/etc/passwd",
    "symlink_outside/secret.key",
    "../project-evil/evil.txt",
    "../../../etc/passwd",
    "safe.txt/../../outside/outside.txt",
    "  ../outside/outside.txt  ",  # Spaces
    "../outside/outside.txt\x00",   # Null byte equivalent in some APIs
])
def test_adversarial_read_file_sandbox_bypass(sandbox_env, payload):
    project_dir, tmp_path = sandbox_env
    set_tools_base_dir(project_dir)
    
    # We want to see if ANY of these payloads can successfully read outside content
    result = ForgeTools.execute_tool("read_file", {"filepath": payload})
    
    # If the tool successfully returns the content of the outside file, the sandbox failed.
    # The sandbox should raise a PermissionError or return an Error string.
    assert "Error" in result or "Access denied" in result or "outside" not in result, f"Sandbox bypass succeeded for payload: {payload}. Result: {result}"

@pytest.mark.parametrize("payload", [
    "../outside/written.txt",
    "/tmp/written.txt",
    "symlink_outside/written.txt",
])
def test_adversarial_write_file_sandbox_bypass(sandbox_env, payload):
    project_dir, tmp_path = sandbox_env
    set_tools_base_dir(project_dir)
    
    result = ForgeTools.execute_tool("write_file", {"filepath": payload, "content": "pwned"})
    
    assert "Error" in result or "Access denied" in result, f"Sandbox write bypass succeeded for payload: {payload}. Result: {result}"
