"""CommitParser — parses git commit messages to extract knowledge."""
from __future__ import annotations

import re
import subprocess
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()

# Keyword patterns for extraction
DECISION_KEYWORDS = [
    r"\bdecided?\b", r"\bchose?\b", r"\badopted?\b", r"\bswitched?\s+to\b",
    r"\binstead\s+of\b", r"\bprefer(?:red|ence)?\b", r"\bRFC\b",
    r"\barchitecture\b", r"\bdesign\s+choice\b", r"\btrade-?off\b",
    r"\bfor\s+now\b", r"\btemporary\b", r"\bworkaround\b",
]

BUG_FIX_KEYWORDS = [
    r"\bfix(?:ed|es)?\b", r"\bbug\b", r"\bresolve[ds]?\b",
    r"\bpatch\b", r"\bcrash(?:ed)?\b", r"\berror\b",
    r"\bfail(?:ed|ure)?\b", r"\bregression\b", r"\bhack\b",
]

PREFERENCE_KEYWORDS = [
    r"\bprefer(?:red|ence)?\b", r"\bconvention\b", r"\bstandard\b",
    r"\bstyle\b", r"\bformat\b", r"\blint\b", r"\bcodestyle\b",
]


@dataclass
class ParsedCommit:
    """A parsed git commit with extracted metadata."""

    sha: str
    message: str
    author_name: str
    author_email: str
    timestamp: str
    parent_shas: list[str]
    files_changed: list[str]


@dataclass
class ExtractionResult:
    """Result of extracting knowledge from a commit."""

    kind: str  # decision, bug, preference
    confidence: float
    data: dict
    dedup_key: str


class CommitParser:
    """Parses git commit messages and extracts decisions, bugs, preferences."""

    def get_commit_history(
        self, repo_path: str, since: str | None = None, limit: int = 1000
    ) -> list[ParsedCommit]:
        """Get commit history from a git repository."""
        try:
            cmd = [
                "git", "log",
                "--pretty=format:%H|%s|%an|%ae|%aI|%P",
                f"-{limit}",
            ]
            if since:
                cmd.append(f"{since}..HEAD")

            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                logger.warning("git_log_failed", error=result.stderr)
                return []

            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 5)
                if len(parts) >= 6:
                    sha = parts[0]
                    message = parts[1]
                    author_name = parts[2]
                    author_email = parts[3]
                    timestamp = parts[4]
                    parent_shas = parts[5].split() if parts[5] else []

                    # Get files changed
                    files = self._get_commit_files(repo_path, sha)

                    commits.append(ParsedCommit(
                        sha=sha,
                        message=message,
                        author_name=author_name,
                        author_email=author_email,
                        timestamp=timestamp,
                        parent_shas=parent_shas,
                        files_changed=files,
                    ))

            return commits

        except Exception as e:
            logger.error("git_history_error", error=str(e))
            return []

    def _get_commit_files(self, repo_path: str, commit_sha: str) -> list[str]:
        """Get files changed in a specific commit."""
        try:
            result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", commit_sha],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return [f for f in result.stdout.strip().split("\n") if f]
            return []
        except Exception:
            return []

    def extract_from_message(
        self, commit: ParsedCommit
    ) -> list[ExtractionResult]:
        """Extract decisions, bugs, and preferences from a commit message."""
        results = []
        message_lower = commit.message.lower()

        # Extract decisions
        decision_confidence = self._check_keywords(message_lower, DECISION_KEYWORDS)
        if decision_confidence > 0:
            # Boost confidence if it's an ADR file
            has_adr = any("adr" in f.lower() or "decision" in f.lower() for f in commit.files_changed)
            if has_adr:
                decision_confidence = min(decision_confidence + 0.2, 1.0)

            results.append(ExtractionResult(
                kind="decision",
                confidence=decision_confidence,
                data={
                    "title": commit.message.split("\n")[0][:200],
                    "rationale": commit.message,
                    "author": commit.author_name,
                },
                dedup_key=self._make_dedup_key("decision", commit.sha),
            ))

        # Extract bug fixes
        bug_confidence = self._check_keywords(message_lower, BUG_FIX_KEYWORDS)
        if bug_confidence > 0:
            results.append(ExtractionResult(
                kind="bug",
                confidence=bug_confidence,
                data={
                    "title": commit.message.split("\n")[0][:200],
                    "fix_commit": commit.sha,
                    "author": commit.author_name,
                },
                dedup_key=self._make_dedup_key("bug", commit.sha),
            ))

        # Extract preferences
        pref_confidence = self._check_keywords(message_lower, PREFERENCE_KEYWORDS)
        if pref_confidence > 0:
            results.append(ExtractionResult(
                kind="preference",
                confidence=pref_confidence,
                data={
                    "key": commit.message.split("\n")[0][:100],
                    "value": commit.message,
                    "author": commit.author_name,
                },
                dedup_key=self._make_dedup_key("preference", commit.sha),
            ))

        return results

    def _check_keywords(self, text: str, keywords: list[str]) -> float:
        """Check if text contains keywords. Returns confidence score."""
        matches = 0
        for pattern in keywords:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1

        if matches == 0:
            return 0.0
        elif matches == 1:
            return 0.6
        elif matches == 2:
            return 0.75
        else:
            return min(0.5 + (matches * 0.1), 0.95)

    def _make_dedup_key(self, kind: str, commit_sha: str) -> str:
        """Create a deduplication key."""
        import hashlib
        return hashlib.sha256(f"{kind}:{commit_sha}".encode()).hexdigest()[:16]
