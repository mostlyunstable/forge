import pytest
import asyncio
from pathlib import Path
from forge.application.agent.tools import get_tools_base_dir, _tools_base_dir, _ALLOWED_BASE_DIR

@pytest.mark.asyncio
async def test_attack_4_project_isolation():
    """Run thousands of concurrent tasks to stress ContextVar isolation."""
    # We will simulate 1000 tasks toggling context vars and sleeping to force event loop swaps.
    
    results = []
    
    async def worker(project_id: int):
        target = Path(f"/tmp/project_{project_id}")
        token = _tools_base_dir.set(target)
        try:
            # Yield to event loop to allow another task to overwrite threadlocals if used
            await asyncio.sleep(0.001)
            
            # Read context
            current = get_tools_base_dir()
            
            # Record result
            results.append(current == target)
            
            # Yield again
            await asyncio.sleep(0.001)
            
            current = get_tools_base_dir()
            results.append(current == target)
            
        finally:
            _tools_base_dir.reset(token)

    # Spawn 1000 tasks
    tasks = [asyncio.create_task(worker(i)) for i in range(1000)]
    await asyncio.gather(*tasks)
    
    # Verify isolation held up for every single read
    assert all(results), "Project isolation leaked across asyncio tasks!"

@pytest.mark.asyncio
async def test_attack_5_contextvar_escape():
    """Test if context is lost in to_thread, which tools often use."""
    
    target = Path(f"/tmp/project_to_thread")
    token = _tools_base_dir.set(target)
    try:
        def blocking_io():
            return get_tools_base_dir()
            
        # ContextVars natively propagate to threads created by asyncio.to_thread
        result = await asyncio.to_thread(blocking_io)
        assert result == target, f"Context lost in to_thread: {result}"
        
        # Test loss after Exception
        try:
            raise ValueError("Something bad")
        except ValueError:
            pass
            
        result_after_exc = get_tools_base_dir()
        assert result_after_exc == target, "Context lost after exception"
        
    finally:
        _tools_base_dir.reset(token)
