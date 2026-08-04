# mypy: disable-error-code="assignment, arg-type"
"""GitDiffProvider — fetches git diffs for PR analysis."""

from __future__ import annotations

from typing import Any

import structlog

from forge.domain.analysis.ports import IDiffProvider
from forge.domain.projects.value_objects.project_id import ProjectId

logger = structlog.get_logger()


class GitDiffProvider(IDiffProvider):
    """Fetches diff data from a local git repository.

    For MVP, this reads from a local repo path.
    In production, this would integrate with GitHub/GitLab APIs.
    """

    def __init__(self, repo_path: str | None = None) -> None:
        self._repo_path = repo_path

    async def get_pr_diff(self, project_id: ProjectId, pr_number: int) -> dict[str, Any]:
        """Get diff for a PR number.

        For MVP, returns a mock/empty diff.
        Production implementation would call GitHub/GitLab API.
        """
        logger.info(
            "git_diff_fetch",
            project_id=str(project_id),
            pr_number=pr_number,
            note="Using stub provider — integrate with GitHub/GitLab API for production",
        )
        # Stub: return empty diff. Production would call API.
        return {
            "title": f"PR #{pr_number}",
            "body": "",
            "files": [],
            "base_sha": "",
            "head_sha": "",
        }

    async def get_commit_diff(
        self, project_id: ProjectId, base_sha: str, head_sha: str
    ) -> dict[str, Any]:
        """Get diff between two commits using local git."""
        if not self._repo_path:
            logger.warning("git_diff_no_repo_path", project_id=str(project_id))
            return {
                "title": f"Diff {base_sha[:8]}..{head_sha[:8]}",
                "body": "",
                "files": [],
                "base_sha": base_sha,
                "head_sha": head_sha,
            }

        try:
            import git

            repo = git.Repo(self._repo_path)
            base = repo.commit(base_sha)
            head = repo.commit(head_sha)
            diff = base.diff(head)

            files = []
            for change in diff:
                file_info = {
                    "file_path": change.a_path or change.b_path or "",
                    "change_type": self._map_change_type(change.change_type),
                    "additions": 0,
                    "deletions": 0,
                    "language": self._detect_language(change.a_path or change.b_path or ""),
                }
                # Try to count lines
                if change.diff:
                    diff_text = change.diff.decode("utf-8", errors="replace")  # type: ignore
                    additions = sum(
                        1
                        for line in diff_text.split("\n")
                        if line.startswith("+") and not line.startswith("+++")
                    )
                    deletions = sum(
                        1
                        for line in diff_text.split("\n")
                        if line.startswith("-") and not line.startswith("---")
                    )
                    file_info["additions"] = additions
                    file_info["deletions"] = deletions

                files.append(file_info)

            return {
                "title": f"Diff {base_sha[:8]}..{head_sha[:8]}",
                "body": "",
                "files": files,
                "base_sha": base_sha,
                "head_sha": head_sha,
            }

        except Exception as e:
            logger.error("git_diff_error", error=str(e), base_sha=base_sha, head_sha=head_sha)
            raise RuntimeError(f"Failed to compute diff: {e}") from e

    def _map_change_type(self, git_type: str) -> str:
        """Map gitpython change type to our ChangeType."""
        mapping = {
            "A": "added",
            "D": "deleted",
            "R": "renamed",
            "M": "modified",
        }
        return mapping.get(git_type, "modified")

    def _detect_language(self, file_path: str) -> str:
        """Detect language from file extension."""
        ext_map = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".rb": "ruby",
        }
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        return ""
