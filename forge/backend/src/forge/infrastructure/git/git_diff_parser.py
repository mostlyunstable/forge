"""GitDiffParser — parses git diffs to extract changed files."""

from __future__ import annotations

import subprocess

import structlog

logger = structlog.get_logger()


class GitDiffParser:
    """Parses git diffs to extract changed files and their metadata."""

    def get_changed_files(self, repo_path: str, from_ref: str, to_ref: str = "HEAD") -> list[dict]:
        """Get files changed between two refs.

        Returns list of dicts with:
        - file_path: str
        - change_type: str (added, modified, deleted, renamed)
        - additions: int
        - deletions: int
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", "--numstat", from_ref, to_ref],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.warning("git_diff_failed", error=result.stderr)
                return []

            files = []
            result.stdout.strip().split("\n")

            # Parse --name-status output
            status_result = subprocess.run(
                ["git", "diff", "--name-status", from_ref, to_ref],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            statuses = {}
            for line in status_result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 2:
                    status = parts[0]
                    file_path = parts[-1]
                    statuses[file_path] = status

            # Parse --numstat output
            numstat_result = subprocess.run(
                ["git", "diff", "--numstat", from_ref, to_ref],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            for line in numstat_result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 3:
                    additions = int(parts[0]) if parts[0] != "-" else 0
                    deletions = int(parts[1]) if parts[1] != "-" else 0
                    file_path = parts[2]

                    change_type = statuses.get(file_path, "modified")
                    # Normalize change types
                    if change_type.startswith("A"):
                        change_type = "added"
                    elif change_type.startswith("D"):
                        change_type = "deleted"
                    elif change_type.startswith("R"):
                        change_type = "renamed"
                    else:
                        change_type = "modified"

                    files.append(
                        {
                            "file_path": file_path,
                            "change_type": change_type,
                            "additions": additions,
                            "deletions": deletions,
                        }
                    )

            return files

        except subprocess.TimeoutExpired:
            logger.warning("git_diff_timeout", repo_path=repo_path)
            return []
        except Exception as e:
            logger.error("git_diff_error", error=str(e))
            return []

    def get_commit_files(self, repo_path: str, commit_sha: str) -> list[dict]:
        """Get files changed in a specific commit."""
        try:
            result = subprocess.run(
                [
                    "git",
                    "diff-tree",
                    "--no-commit-id",
                    "-r",
                    "--name-status",
                    "--numstat",
                    commit_sha,
                ],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return []

            files = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 3:
                    status = parts[0]
                    file_path = parts[2]

                    if status.startswith("A"):
                        change_type = "added"
                    elif status.startswith("D"):
                        change_type = "deleted"
                    elif status.startswith("R"):
                        change_type = "renamed"
                    else:
                        change_type = "modified"

                    files.append(
                        {
                            "file_path": file_path,
                            "change_type": change_type,
                        }
                    )

            return files

        except Exception as e:
            logger.error("git_commit_files_error", error=str(e))
            return []

    def get_latest_commit(self, repo_path: str) -> str | None:
        """Get the latest commit SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
