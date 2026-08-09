import asyncio
import os
import pytest
import shutil
from pathlib import Path

from forge.application.agent.tools import (
    set_tools_base_dir,
    get_tools_base_dir,
    ForgeTools,
    _ALLOWED_BASE_DIR,
)

@pytest.fixture
def adversarial_projects(tmp_path):
    project_a = tmp_path / "project_a"
    project_b = tmp_path / "project_b"
    project_c = tmp_path / "project_c"
    project_a.mkdir()
    project_b.mkdir()
    project_c.mkdir()
    
    # Write some initial files
    (project_a / "secret_a.txt").write_text("this belongs to A")
    (project_b / "secret_b.txt").write_text("this belongs to B")
    (project_c / "secret_c.txt").write_text("this belongs to C")
    
    yield project_a, project_b, project_c
    
    if project_a.exists():
        shutil.rmtree(project_a)
    if project_b.exists():
        shutil.rmtree(project_b)
    if project_c.exists():
        shutil.rmtree(project_c)

@pytest.mark.asyncio
async def test_adversarial_project_isolation_threading_local(adversarial_projects):
    """
    Attempt to violate project isolation by creating a race condition
    in an async context. We expect this to FAIL (meaning no violations) 
    now that contextvars is used.
    """
    project_a, project_b, project_c = adversarial_projects
    
    iterations = 200
    violations = []

    async def run_project_task(project_dir, expected_secret, disallowed_secrets):
        for _ in range(iterations):
            set_tools_base_dir(project_dir)
            
            # Yield to event loop
            await asyncio.sleep(0.001)
            
            try:
                # Nested task
                async def nested_read():
                    await asyncio.sleep(0)
                    return ForgeTools.execute_tool("run_shell_command", {"command": "ls"})
                
                result = await asyncio.wait_for(nested_read(), timeout=5.0)
                
                if expected_secret not in result:
                    violations.append(f"Expected {expected_secret} not found in {project_dir}")
                for ds in disallowed_secrets:
                    if ds in result:
                        violations.append(f"Leak! Found {ds} in context of {project_dir}. Base dir reported: {get_tools_base_dir()}")
            except Exception as e:
                pass

    tasks = [
        run_project_task(project_a, "secret_a.txt", ["secret_b.txt", "secret_c.txt"]),
        run_project_task(project_b, "secret_b.txt", ["secret_a.txt", "secret_c.txt"]),
        run_project_task(project_c, "secret_c.txt", ["secret_a.txt", "secret_b.txt"]),
    ]
    
    await asyncio.gather(*tasks)
    
    assert len(violations) == 0, f"Failed! Found {len(violations)} project isolation violations: {violations[:5]}"
