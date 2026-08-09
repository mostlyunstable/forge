from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from git import InvalidGitRepositoryError

from forge.domain.git.value_objects.commit_classification import CommitClassification
from forge.infrastructure.git.git_analyzer import CommitClassifier, GitAnalyzer


def test_commit_classifier():
    classifier = CommitClassifier()
    assert classifier.classify("fix: bug in parser") == CommitClassification.BUGFIX
    assert classifier.classify("feat(ui): add new button") == CommitClassification.FEATURE
    assert classifier.classify("refactor: clean up messy code") == CommitClassification.REFACTOR
    assert classifier.classify("perf: optimize query") == CommitClassification.PERFORMANCE
    assert classifier.classify("security: fix vulnerability") == CommitClassification.SECURITY
    assert classifier.classify("Update documentation") == CommitClassification.OTHER

    # Keyword fallbacks
    assert classifier.classify("fixed a bug in the code") == CommitClassification.BUGFIX
    assert classifier.classify("implement new feature") == CommitClassification.FEATURE

def test_git_analyzer_init_success():
    with patch("forge.infrastructure.git.git_analyzer.Repo") as MockRepo:
        _ = GitAnalyzer("/path/to/repo")
        MockRepo.assert_called_once_with("/path/to/repo")

def test_git_analyzer_init_failure():
    with patch("forge.infrastructure.git.git_analyzer.Repo", side_effect=InvalidGitRepositoryError):
        with pytest.raises(ValueError, match="Not a valid git repository"):
            GitAnalyzer("/invalid/path")

def test_git_analyzer_get_commit_history():
    with patch("forge.infrastructure.git.git_analyzer.Repo") as MockRepo:
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.hexsha = "sha1"
        mock_commit.message = "fix: crash"
        mock_commit.author = "Test Author"
        mock_commit.committed_date = 1600000000
        mock_commit.stats.files = {"main.py": {}}

        mock_repo.iter_commits.return_value = [mock_commit]
        MockRepo.return_value = mock_repo

        analyzer = GitAnalyzer("/repo")
        history = analyzer.get_commit_history()

        assert len(history) == 1
        assert history[0]["sha"] == "sha1"
        assert history[0]["message"] == "fix: crash"
        assert history[0]["author"] == "Test Author"
        assert history[0]["classification"] == "bugfix"
        assert history[0]["files_changed"] == ["main.py"]
        assert history[0]["timestamp"] == datetime.fromtimestamp(1600000000, tz=UTC)

def test_git_analyzer_get_technologies():
    with patch("forge.infrastructure.git.git_analyzer.Repo"):
        with patch("forge.infrastructure.git.git_analyzer.Path.walk") as mock_walk:
            # yield (root, dirs, files)
            mock_walk.return_value = [
                ("/repo", [], ["package.json", "main.py", "index.tsx", "README.md", "app.rb"])
            ]
            analyzer = GitAnalyzer("/repo")
            techs = analyzer.get_technologies()
            assert sorted(techs) == sorted(["Node.js", "Python", "TypeScript", "Ruby"])

def test_git_analyzer_get_technologies_error():
    with patch("forge.infrastructure.git.git_analyzer.Repo"):
        with patch("forge.infrastructure.git.git_analyzer.Path.walk", side_effect=PermissionError):
            analyzer = GitAnalyzer("/repo")
            assert analyzer.get_technologies() == []

def test_git_analyzer_get_repository_stats_empty():
    with patch("forge.infrastructure.git.git_analyzer.Repo") as MockRepo:
        mock_repo = MagicMock()
        mock_repo.iter_commits.return_value = []
        MockRepo.return_value = mock_repo

        analyzer = GitAnalyzer("/repo")
        stats = analyzer.get_repository_stats()

        assert stats["total_commits"] == 0
        assert stats["technologies"] == []

def test_git_analyzer_get_repository_stats():
    with patch("forge.infrastructure.git.git_analyzer.Repo") as MockRepo:
        mock_repo = MagicMock()

        mock_commit_old = MagicMock()
        mock_commit_old.committed_date = 1600000000

        mock_commit_new = MagicMock()
        mock_commit_new.committed_date = 1600001000

        # iter_commits returns from newest to oldest
        mock_repo.iter_commits.return_value = [mock_commit_new, mock_commit_old]
        MockRepo.return_value = mock_repo

        analyzer = GitAnalyzer("/repo")

        with patch.object(analyzer, "get_technologies", return_value=["Python"]):
            stats = analyzer.get_repository_stats()

            assert stats["total_commits"] == 2
            assert stats["technologies"] == ["Python"]
            assert stats["first_commit"] == datetime.fromtimestamp(1600000000, tz=UTC).isoformat()
            assert stats["last_commit"] == datetime.fromtimestamp(1600001000, tz=UTC).isoformat()
