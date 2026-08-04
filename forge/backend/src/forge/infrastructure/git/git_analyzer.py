"""GitAnalyzer - analyzes git repositories for commit intelligence."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from git import InvalidGitRepositoryError, Repo

from forge.domain.git.value_objects.commit_classification import CommitClassification


class CommitClassifier:
    """Classifies commit messages into categories using regex patterns."""

    _PATTERNS: dict[CommitClassification, list[str]] = {
        CommitClassification.BUGFIX: [
            r"^fix[\(:]",
            r"^bugfix[\(:]",
            r"^bug[\(:]",
            r"^patch[\(:]",
            r"^resolve[\(:]",
        ],
        CommitClassification.FEATURE: [
            r"^feat[\(:]",
            r"^add[\(:]",
            r"^implement[\(:]",
            r"^new[\(:]",
            r"^feature[\(:]",
        ],
        CommitClassification.REFACTOR: [
            r"^refactor[\(:]",
            r"^cleanup[\(:]",
            r"^clean[\(:]",
            r"^restructure[\(:]",
        ],
        CommitClassification.PERFORMANCE: [
            r"^perf[\(:]",
            r"^performance[\(:]",
            r"^optimize[\(:]",
        ],
        CommitClassification.SECURITY: [
            r"^security[\(:]",
            r"^sec[\(:]",
            r"^auth[\(:]",
            r"^permission[\(:]",
        ],
    }

    @classmethod
    def classify(cls, message: str) -> CommitClassification:
        lower = message.lower()
        for classification, patterns in cls._PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, lower):
                    return classification

        if any(w in lower for w in ["fix", "bug", "error"]):
            return CommitClassification.BUGFIX
        if any(w in lower for w in ["add", "new", "implement"]):
            return CommitClassification.FEATURE
        return CommitClassification.OTHER


class GitAnalyzer:
    """Analyzes a git repository and extracts commit intelligence."""

    def __init__(self, repo_path: str) -> None:
        self._repo_path = Path(repo_path)
        try:
            self._repo = Repo(repo_path)
        except InvalidGitRepositoryError as e:
            raise ValueError(f"Not a valid git repository: {repo_path}") from e
        self._classifier = CommitClassifier()

    def get_commit_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Retrieve classified commit history."""
        commits = []
        for commit in self._repo.iter_commits(max_count=limit):
            classification = self._classifier.classify(commit.message)  # type: ignore
            commits.append(
                {
                    "sha": commit.hexsha,
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "timestamp": datetime.fromtimestamp(commit.committed_date, tz=UTC),
                    "files_changed": list(commit.stats.files.keys()),
                    "classification": classification.value,
                }
            )
        return commits

    def get_technologies(self) -> list[str]:
        """Detect technologies used in the repository."""
        tech_map = {
            "package.json": "Node.js",
            "requirements.txt": "Python",
            "Cargo.toml": "Rust",
            "go.mod": "Go",
            "pom.xml": "Java",
            "Gemfile": "Ruby",
            "composer.json": "PHP",
        }
        ext_map = {
            ".py": "Python",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".rs": "Rust",
            ".go": "Go",
            ".java": "Java",
            ".rb": "Ruby",
        }

        technologies: set[str] = set()
        try:
            for root, _dirs, files in self._repo_path.walk():
                for file in files:
                    if file in tech_map:
                        technologies.add(tech_map[file])
                    ext = Path(file).suffix.lower()
                    if ext in ext_map:
                        technologies.add(ext_map[ext])
        except (PermissionError, OSError):
            pass

        return sorted(technologies)

    def get_repository_stats(self) -> dict[str, Any]:
        """Get high-level repository statistics."""
        commits = list(self._repo.iter_commits())
        if not commits:
            return {"total_commits": 0, "technologies": []}

        return {
            "total_commits": len(commits),
            "technologies": self.get_technologies(),
            "first_commit": datetime.fromtimestamp(commits[-1].committed_date, tz=UTC).isoformat(),
            "last_commit": datetime.fromtimestamp(commits[0].committed_date, tz=UTC).isoformat(),
        }
