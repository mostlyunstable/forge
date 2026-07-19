import pytest
from forge.infrastructure.code_indexer.tree_sitter_parser import TreeSitterParser

def test_semantic_chunking_python():
    parser = TreeSitterParser()
    content = """
def test_func():
    pass

class TestClass:
    def method_one(self):
        return 1
"""
    results = parser.parse_file("test.py", content)
    
    # Check that it extracted the function and the class
    names = [r.name for r in results]
    assert "test_func" in names
    assert "TestClass" in names
    
def test_semantic_chunking_markdown():
    parser = TreeSitterParser()
    content = """
# Header 1
Some content here
## Header 2
More content
"""
    results = parser.parse_file("test.md", content)
    
    # Should extract headers/sections based on markdown parser
    names = [r.name for r in results]
    assert "Header 1" in names
    assert "Header 2" in names
