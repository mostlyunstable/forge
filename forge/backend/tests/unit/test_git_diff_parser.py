import subprocess
from unittest.mock import MagicMock, patch

import pytest

from forge.infrastructure.git.git_diff_parser import GitDiffParser


@pytest.fixture
def parser():
    return GitDiffParser()

def test_get_changed_files_success(parser):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="A\tadded.py\n10\t0\tadded.py"),
            MagicMock(returncode=0, stdout="A\tadded.py\nM\tmod.py\nD\tdel.py\nR100\told.py\tnew.py"),
            MagicMock(returncode=0, stdout="10\t0\tadded.py\n2\t2\tmod.py\n0\t5\tdel.py\n-\t-\tnew.py")
        ]

        files = parser.get_changed_files("/repo", "HEAD~1", "HEAD")
        assert len(files) == 4

        # Check added
        assert files[0]["file_path"] == "added.py"
        assert files[0]["change_type"] == "added"
        assert files[0]["additions"] == 10
        assert files[0]["deletions"] == 0

        # Check modified
        assert files[1]["file_path"] == "mod.py"
        assert files[1]["change_type"] == "modified"
        assert files[1]["additions"] == 2
        assert files[1]["deletions"] == 2

        # Check deleted
        assert files[2]["file_path"] == "del.py"
        assert files[2]["change_type"] == "deleted"
        assert files[2]["additions"] == 0
        assert files[2]["deletions"] == 5

        # Check renamed (binary or no numstat)
        assert files[3]["file_path"] == "new.py"
        assert files[3]["change_type"] == "renamed"
        assert files[3]["additions"] == 0
        assert files[3]["deletions"] == 0

def test_get_changed_files_failure(parser):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="fatal error")
        files = parser.get_changed_files("/repo", "HEAD~1")
        assert files == []

def test_get_changed_files_timeout(parser):
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="git", timeout=30)):
        files = parser.get_changed_files("/repo", "HEAD~1")
        assert files == []

def test_get_changed_files_exception(parser):
    with patch("subprocess.run", side_effect=Exception("unexpected")):
        files = parser.get_changed_files("/repo", "HEAD~1")
        assert files == []

def test_get_commit_files_success(parser):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="A\t\tadded.py\nM\t\tmod.py\nD\t\tdel.py\nR100\told.py\tnew.py\nX\t\tunknown.py"
        )
        files = parser.get_commit_files("/repo", "sha123")
        assert len(files) == 5
        assert files[0]["change_type"] == "added"
        assert files[0]["file_path"] == "added.py"
        assert files[1]["change_type"] == "modified"
        assert files[2]["change_type"] == "deleted"
        assert files[3]["change_type"] == "renamed"
        assert files[4]["change_type"] == "modified"

def test_get_commit_files_failure(parser):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        assert parser.get_commit_files("/repo", "sha123") == []

def test_get_commit_files_exception(parser):
    with patch("subprocess.run", side_effect=Exception("boom")):
        assert parser.get_commit_files("/repo", "sha123") == []

def test_get_latest_commit_success(parser):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="abcdef123456\n")
        assert parser.get_latest_commit("/repo") == "abcdef123456"

def test_get_latest_commit_failure(parser):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        assert parser.get_latest_commit("/repo") is None

def test_get_latest_commit_exception(parser):
    with patch("subprocess.run", side_effect=Exception("boom")):
        assert parser.get_latest_commit("/repo") is None
