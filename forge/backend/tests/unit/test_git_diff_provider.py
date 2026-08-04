import uuid
import pytest
from unittest.mock import patch, MagicMock

from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure.analysis.git_diff_provider import GitDiffProvider

@pytest.fixture
def provider():
    return GitDiffProvider(repo_path="/fake/repo")

@pytest.mark.asyncio
async def test_get_pr_diff(provider):
    project_id = ProjectId(uuid.uuid4())
    result = await provider.get_pr_diff(project_id, 123)
    
    assert result["title"] == "PR #123"
    assert result["body"] == ""
    assert result["files"] == []
    assert result["base_sha"] == ""
    assert result["head_sha"] == ""

@pytest.mark.asyncio
async def test_get_commit_diff_no_repo_path():
    provider_no_repo = GitDiffProvider(repo_path=None)
    project_id = ProjectId(uuid.uuid4())
    
    result = await provider_no_repo.get_commit_diff(project_id, "base123", "head456")
    assert result["base_sha"] == "base123"
    assert result["head_sha"] == "head456"
    assert result["title"] == "Diff base123..head456"
    assert result["files"] == []

@pytest.mark.asyncio
async def test_get_commit_diff_success(provider):
    project_id = ProjectId(uuid.uuid4())
    
    mock_change_1 = MagicMock()
    mock_change_1.a_path = "src/main.py"
    mock_change_1.b_path = "src/main.py"
    mock_change_1.change_type = "M"
    mock_change_1.diff = b"+++ b/src/main.py\n--- a/src/main.py\n+add1\n+add2\n-del1"
    
    mock_change_2 = MagicMock()
    mock_change_2.a_path = None
    mock_change_2.b_path = "new_file.js"
    mock_change_2.change_type = "A"
    mock_change_2.diff = b"+++ b/new_file.js\n+add1"

    mock_diff = [mock_change_1, mock_change_2]
    
    mock_head = MagicMock()
    mock_base = MagicMock()
    mock_base.diff.return_value = mock_diff
    
    mock_repo = MagicMock()
    # repo.commit returns different commits
    mock_repo.commit.side_effect = lambda sha: mock_base if sha == "base123" else mock_head
    
    with patch("git.Repo", return_value=mock_repo):
        result = await provider.get_commit_diff(project_id, "base123", "head456")
        
        assert result["base_sha"] == "base123"
        assert result["head_sha"] == "head456"
        assert len(result["files"]) == 2
        
        file1 = result["files"][0]
        assert file1["file_path"] == "src/main.py"
        assert file1["change_type"] == "modified"
        assert file1["language"] == "python"
        assert file1["additions"] == 2
        assert file1["deletions"] == 1
        
        file2 = result["files"][1]
        assert file2["file_path"] == "new_file.js"
        assert file2["change_type"] == "added"
        assert file2["language"] == "javascript"
        assert file2["additions"] == 1
        assert file2["deletions"] == 0

@pytest.mark.asyncio
async def test_get_commit_diff_git_error(provider):
    project_id = ProjectId(uuid.uuid4())
    
    with patch("git.Repo", side_effect=Exception("Git not found")):
        with pytest.raises(RuntimeError) as exc:
            await provider.get_commit_diff(project_id, "base123", "head456")
        assert "Failed to compute diff: Git not found" in str(exc.value)

def test_map_change_type(provider):
    assert provider._map_change_type("A") == "added"
    assert provider._map_change_type("D") == "deleted"
    assert provider._map_change_type("R") == "renamed"
    assert provider._map_change_type("M") == "modified"
    assert provider._map_change_type("Z") == "modified" # fallback

def test_detect_language(provider):
    assert provider._detect_language("test.py") == "python"
    assert provider._detect_language("test.ts") == "typescript"
    assert provider._detect_language("test.tsx") == "typescript"
    assert provider._detect_language("test.js") == "javascript"
    assert provider._detect_language("test.jsx") == "javascript"
    assert provider._detect_language("test.go") == "go"
    assert provider._detect_language("test.rs") == "rust"
    assert provider._detect_language("test.java") == "java"
    assert provider._detect_language("test.rb") == "ruby"
    assert provider._detect_language("test.unknown") == ""
    assert provider._detect_language("Makefile") == ""
