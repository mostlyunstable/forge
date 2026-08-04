import subprocess
from unittest.mock import patch, MagicMock

import pytest

from forge.infrastructure.git.commit_parser import CommitParser, ParsedCommit

@pytest.fixture
def parser():
    return CommitParser()

def test_get_commit_history_success(parser):
    with patch("subprocess.run") as mock_run, patch.object(parser, "_get_commit_files") as mock_get_files:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="sha1|msg1|Author 1|author1@test.com|2023-01-01T00:00:00Z|\nsha2|msg2|Author 2|author2@test.com|2023-01-02T00:00:00Z|sha1\n"
        )
        mock_get_files.return_value = ["file1.py"]

        commits = parser.get_commit_history("/repo", since="HEAD~1")
        assert len(commits) == 2
        
        assert commits[0].sha == "sha1"
        assert commits[0].message == "msg1"
        assert commits[0].parent_shas == []
        assert commits[0].files_changed == ["file1.py"]

        assert commits[1].sha == "sha2"
        assert commits[1].message == "msg2"
        assert commits[1].parent_shas == ["sha1"]

def test_get_commit_history_failure(parser):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        assert parser.get_commit_history("/repo") == []

def test_get_commit_history_exception(parser):
    with patch("subprocess.run", side_effect=Exception("boom")):
        assert parser.get_commit_history("/repo") == []

def test_get_commit_files_success(parser):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="file1.py\nfile2.py\n")
        assert parser._get_commit_files("/repo", "sha1") == ["file1.py", "file2.py"]

def test_get_commit_files_failure(parser):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        assert parser._get_commit_files("/repo", "sha1") == []

def test_get_commit_files_exception(parser):
    with patch("subprocess.run", side_effect=Exception("boom")):
        assert parser._get_commit_files("/repo", "sha1") == []

def test_get_file_metadata_success(parser):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="sha1|Author 1|HEAD -> main, origin/main\n"
        )
        meta = parser.get_file_metadata("/repo", "file1.py")
        assert meta["git_commit"] == "sha1"
        assert meta["git_author"] == "Author 1"
        assert meta["git_branch"] == "main"

def test_get_file_metadata_no_branch(parser):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="sha1|Author 1|\n"
        )
        meta = parser.get_file_metadata("/repo", "file1.py")
        assert meta["git_commit"] == "sha1"
        assert meta["git_author"] == "Author 1"
        assert meta["git_branch"] == ""

def test_get_file_metadata_failure(parser):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        assert parser.get_file_metadata("/repo", "file1.py") == {}

def test_get_file_metadata_exception(parser):
    with patch("subprocess.run", side_effect=Exception("boom")):
        assert parser.get_file_metadata("/repo", "file1.py") == {}

def test_extract_from_message(parser):
    commit_dec = ParsedCommit(
        sha="sha1", message="Decided to use fast API instead of flask", author_name="A", author_email="a@a.com",
        timestamp="t", parent_shas=[], files_changed=["adr/0001-fastapi.md"]
    )
    commit_bug = ParsedCommit(
        sha="sha2", message="Fixes crash on startup", author_name="A", author_email="a@a.com",
        timestamp="t", parent_shas=[], files_changed=["main.py"]
    )
    commit_pref = ParsedCommit(
        sha="sha3", message="The convention is to use ruff", author_name="A", author_email="a@a.com",
        timestamp="t", parent_shas=[], files_changed=["pyproject.toml"]
    )
    commit_none = ParsedCommit(
        sha="sha4", message="Update docs", author_name="A", author_email="a@a.com",
        timestamp="t", parent_shas=[], files_changed=["README.md"]
    )

    res_dec = parser.extract_from_message(commit_dec)
    assert len(res_dec) == 1
    assert res_dec[0].kind == "decision"
    assert res_dec[0].confidence > 0.5  # boosted by adr

    res_bug = parser.extract_from_message(commit_bug)
    assert len(res_bug) == 1
    assert res_bug[0].kind == "bug"
    assert res_bug[0].confidence > 0.5

    res_pref = parser.extract_from_message(commit_pref)
    assert len(res_pref) == 1
    assert res_pref[0].kind == "preference"
    assert res_pref[0].confidence > 0.5

    res_none = parser.extract_from_message(commit_none)
    assert len(res_none) == 0
