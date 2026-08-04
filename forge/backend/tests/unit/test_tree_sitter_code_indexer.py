import os
import uuid
from unittest.mock import patch, MagicMock, AsyncMock, mock_open

import pytest

from forge.infrastructure.code_indexer.tree_sitter_code_indexer import TreeSitterCodeIndexer
from forge.domain.code.value_objects.entry_type import EntryType

@pytest.fixture
def mock_vector_store():
    store = MagicMock()
    store.upsert_code = AsyncMock()
    return store

@pytest.fixture
def indexer(mock_vector_store):
    with patch("forge.infrastructure.code_indexer.tree_sitter_code_indexer.EmbeddingService") as MockEmbed:
        embed_service = MagicMock()
        async def mock_get_embeddings(texts):
            return [[0.1, 0.2] for _ in texts]
        
        embed_service.get_embeddings = AsyncMock(side_effect=mock_get_embeddings)
        embed_service.get_embedding = AsyncMock(return_value=[0.3, 0.4])
        MockEmbed.return_value = embed_service
        
        with patch("forge.infrastructure.code_indexer.tree_sitter_code_indexer.TreeSitterParser") as MockParser:
            parser = MagicMock()
            MockParser.return_value = parser
            
            yield TreeSitterCodeIndexer(vector_store=mock_vector_store)

@pytest.mark.asyncio
async def test_index_directory(indexer, mock_vector_store):
    pid = uuid.uuid4()
    
    mock_parsed = MagicMock()
    mock_parsed.name = "MyClass"
    mock_parsed.entry_type = EntryType.CLASS
    mock_parsed.content = "class MyClass: pass"
    mock_parsed.language = "python"
    mock_parsed.start_line = 1
    mock_parsed.end_line = 2
    mock_parsed.metadata = {"foo": "bar"}
    
    indexer._parser.parse_file.return_value = [mock_parsed]
    
    # Mock os.walk, os.path.realpath
    def mock_realpath(path):
        return path

    with patch("os.walk") as mock_walk, patch("os.path.realpath", side_effect=mock_realpath), patch("builtins.open", mock_open(read_data="class MyClass: pass")):
        mock_walk.return_value = [
            ("/repo", [".git", "node_modules", "src"], ["main.py", ".env"]),
            ("/repo/src", [], ["app.py"])
        ]
        
        # Test gitignore mock
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="*.env\n")):
                entries = await indexer.index(pid, "/repo")
                
                # Should skip .git and .env, index main.py and app.py
                assert len(entries) == 2
                assert entries[0].file_path.value == "main.py"
                assert entries[1].file_path.value == "src/app.py"
                
                assert mock_vector_store.upsert_code.call_count == 2
                assert indexer._embedding_service.get_embeddings.call_count == 1

@pytest.mark.asyncio
async def test_index_files(indexer, mock_vector_store):
    pid = uuid.uuid4()
    
    mock_parsed = MagicMock()
    mock_parsed.name = "Func"
    mock_parsed.entry_type = EntryType.FUNCTION
    mock_parsed.content = "def f(): pass"
    mock_parsed.language = "python"
    mock_parsed.start_line = 1
    mock_parsed.end_line = 2
    mock_parsed.metadata = {}
    
    indexer._parser.parse_file.return_value = [mock_parsed]
    
    def mock_realpath(path):
        return path
        
    with patch("os.path.realpath", side_effect=mock_realpath), patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data="def f(): pass")):
        
        # We need more than 50 files to test batch flushing
        files = [f"file_{i}.py" for i in range(55)]
        
        entries = await indexer.index_files(pid, "/repo", files)
        
        assert len(entries) == 55
        
        # 55 items -> one flush at 50, one flush at end
        assert indexer._embedding_service.get_embeddings.call_count == 2
        assert mock_vector_store.upsert_code.call_count == 55

@pytest.mark.asyncio
async def test_index_files_fallback_embedding(indexer, mock_vector_store):
    pid = uuid.uuid4()
    
    mock_parsed = MagicMock()
    mock_parsed.name = "Func"
    mock_parsed.entry_type = EntryType.FUNCTION
    mock_parsed.content = "def f(): pass"
    mock_parsed.language = "python"
    mock_parsed.start_line = 1
    mock_parsed.end_line = 2
    mock_parsed.metadata = {}
    
    indexer._parser.parse_file.return_value = [mock_parsed]
    indexer._embedding_service.get_embeddings.side_effect = Exception("Batch timeout")
    indexer._embedding_service.get_embedding.return_value = [0.9]
    
    def mock_realpath(path):
        return path
        
    with patch("os.path.realpath", side_effect=mock_realpath), patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data="def f(): pass")):
        
        files = ["main.py"]
        
        entries = await indexer.index_files(pid, "/repo", files)
        
        assert len(entries) == 1
        assert indexer._embedding_service.get_embeddings.call_count == 1
        assert indexer._embedding_service.get_embedding.call_count == 1
        assert mock_vector_store.upsert_code.call_count == 1

@pytest.mark.asyncio
async def test_index_files_single_fallback_failure(indexer, mock_vector_store):
    pid = uuid.uuid4()
    
    mock_parsed = MagicMock()
    mock_parsed.name = "Func"
    mock_parsed.entry_type = EntryType.FUNCTION
    mock_parsed.content = "def f(): pass"
    mock_parsed.language = "python"
    mock_parsed.start_line = 1
    mock_parsed.end_line = 2
    mock_parsed.metadata = {}
    
    indexer._parser.parse_file.return_value = [mock_parsed]
    indexer._embedding_service.get_embeddings.side_effect = Exception("Batch timeout")
    indexer._embedding_service.get_embedding.side_effect = Exception("Single timeout")
    
    def mock_realpath(path):
        return path
        
    with patch("os.path.realpath", side_effect=mock_realpath), patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data="def f(): pass")):
        files = ["main.py"]
        entries = await indexer.index_files(pid, "/repo", files)
        assert len(entries) == 1
        assert mock_vector_store.upsert_code.call_count == 0

@pytest.mark.asyncio
async def test_index_file_error(indexer, mock_vector_store):
    pid = uuid.uuid4()
    
    def mock_realpath(path):
        return path
        
    with patch("os.path.realpath", side_effect=mock_realpath), patch("os.path.exists", return_value=True), patch("builtins.open", side_effect=Exception("Read error")):
        files = ["main.py"]
        entries = await indexer.index_files(pid, "/repo", files)
        assert len(entries) == 0

@pytest.mark.asyncio
async def test_index_directory_escapes_repo(indexer, mock_vector_store):
    pid = uuid.uuid4()
    
    def mock_realpath(path):
        if "outside" in path:
            return "/outside/path"
        return path

    with patch("os.walk") as mock_walk, patch("os.path.realpath", side_effect=mock_realpath):
        mock_walk.return_value = [
            ("/repo", ["outside_dir"], ["outside_file.py"])
        ]
        entries = await indexer.index(pid, "/repo")
        assert len(entries) == 0

@pytest.mark.asyncio
async def test_index_directory_gitignore_error(indexer, mock_vector_store):
    pid = uuid.uuid4()
    
    def mock_realpath(path):
        return path

    with patch("os.walk") as mock_walk, patch("os.path.realpath", side_effect=mock_realpath):
        mock_walk.return_value = [("/repo", [], ["main.py"])]
        with patch("os.path.exists", return_value=True), patch("builtins.open", side_effect=Exception("Perm error")):
            # It should gracefully swallow the gitignore read error
            entries = await indexer.index(pid, "/repo")
            assert len(entries) == 0

@pytest.mark.asyncio
async def test_index_files_not_exists(indexer, mock_vector_store):
    pid = uuid.uuid4()
    
    def mock_realpath(path):
        return path

    with patch("os.path.realpath", side_effect=mock_realpath), patch("os.path.exists", return_value=False):
        entries = await indexer.index_files(pid, "/repo", ["missing.py"])
        assert len(entries) == 0

@pytest.mark.asyncio
async def test_index_files_commit_parser(indexer, mock_vector_store):
    pid = uuid.uuid4()
    mock_parser = MagicMock()
    mock_parser.get_file_metadata.return_value = {"git_commit": "sha123"}
    
    mock_parsed = MagicMock()
    mock_parsed.name = "Func"
    mock_parsed.entry_type = EntryType.FUNCTION
    mock_parsed.content = "def f(): pass"
    mock_parsed.language = "python"
    mock_parsed.start_line = 1
    mock_parsed.end_line = 2
    mock_parsed.metadata = {}
    
    indexer._parser.parse_file.return_value = [mock_parsed]
    
    def mock_realpath(path):
        return path

    with patch("os.path.realpath", side_effect=mock_realpath), patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data="def f(): pass")):
        entries = await indexer.index_files(pid, "/repo", ["main.py"], commit_parser=mock_parser)
        assert len(entries) == 1
        assert entries[0].metadata["git_commit"] == "sha123"

@pytest.mark.asyncio
async def test_index_directory_file_parse_error(indexer, mock_vector_store):
    pid = uuid.uuid4()
    
    indexer._parser.parse_file.side_effect = Exception("Parse error")
    
    def mock_realpath(path):
        return path

    with patch("os.walk") as mock_walk, patch("os.path.realpath", side_effect=mock_realpath), patch("builtins.open", mock_open(read_data="error code")):
        mock_walk.return_value = [("/repo", [], ["main.py"])]
        
        with patch("os.path.exists", return_value=False):
            entries = await indexer.index(pid, "/repo")
            assert len(entries) == 0

@pytest.mark.asyncio
async def test_index_files_escapes_repo(indexer, mock_vector_store):
    pid = uuid.uuid4()
    
    def mock_realpath(path):
        if "outside" in path:
            return "/outside/path"
        return path

    with patch("os.path.realpath", side_effect=mock_realpath):
        entries = await indexer.index_files(pid, "/repo", ["../outside_file.py"])
        assert len(entries) == 0
