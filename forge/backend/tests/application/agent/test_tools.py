import json

import pytest

from forge.application.agent.tools import ForgeTools


def test_search_web():
    schemas = ForgeTools.get_tool_schemas()
    search_schema = next((s for s in schemas if s["function"]["name"] == "search_web"), None)
    assert search_schema is not None, "search_web schema missing"

    # execute_tool test for search_web (mocked or actual)
    result = ForgeTools.execute_tool("search_web", {"query": "test query python duckduckgo"})
    assert isinstance(result, str)
    try:
        parsed = json.loads(result)
        assert isinstance(parsed, list)
    except json.JSONDecodeError:
        pytest.fail("search_web result should be valid JSON")


def test_run_python_code():
    schemas = ForgeTools.get_tool_schemas()
    run_schema = next((s for s in schemas if s["function"]["name"] == "run_python_code"), None)
    assert run_schema is not None, "run_python_code schema missing"

    # Test valid python code
    result = ForgeTools.execute_tool("run_python_code", {"code": "print('hello world')"})
    assert "hello world" in result

    # Test invalid python code
    result_err = ForgeTools.execute_tool("run_python_code", {"code": "print(1/0)"})
    assert "ZeroDivisionError" in result_err
