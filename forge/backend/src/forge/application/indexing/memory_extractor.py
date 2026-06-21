"""MemoryExtractor — extracts decisions, bugs, preferences from code and commits."""
from __future__ import annotations

import hashlib
import re
from uuid import UUID

from forge.domain.indexing.entities.extraction_candidate import ExtractionCandidate


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

# Code comment patterns
TODO_PATTERN = re.compile(r"#\s*TODO:?\s*(.+)", re.IGNORECASE)
FIXME_PATTERN = re.compile(r"#\s*FIXME:?\s*(.+)", re.IGNORECASE)
HACK_PATTERN = re.compile(r"#\s*HACK:?\s*(.+)", re.IGNORECASE)
NOTE_PATTERN = re.compile(r"#\s*NOTE:?\s*(.+)", re.IGNORECASE)
IMPORTANT_PATTERN = re.compile(r"#\s*IMPORTANT:?\s*(.+)", re.IGNORECASE)


class MemoryExtractor:
    """Extracts decisions, bugs, and preferences from code and commits.

    Two-phase extraction:
    1. Extract candidates (no side effects, idempotent)
    2. Accept candidates into knowledge base (with dedup)
    """

    def extract_from_commit_message(
        self,
        job_id: UUID,
        commit_sha: str,
        message: str,
        author_name: str,
        files_changed: list[str],
    ) -> list[ExtractionCandidate]:
        """Extract candidates from a commit message."""
        candidates = []
        message_lower = message.lower()

        # Extract decisions
        decision_confidence = self._check_keywords(message_lower, DECISION_KEYWORDS)
        if decision_confidence > 0:
            has_adr = any(
                "adr" in f.lower() or "decision" in f.lower()
                for f in files_changed
            )
            if has_adr:
                decision_confidence = min(decision_confidence + 0.2, 1.0)

            candidates.append(ExtractionCandidate.create(
                job_id=job_id,
                kind="decision",
                confidence=decision_confidence,
                data={
                    "title": message.split("\n")[0][:200],
                    "rationale": message,
                    "author": author_name,
                },
                source_commit=commit_sha,
                dedup_key=self._make_dedup_key("decision", commit_sha),
            ))

        # Extract bug fixes
        bug_confidence = self._check_keywords(message_lower, BUG_FIX_KEYWORDS)
        if bug_confidence > 0:
            candidates.append(ExtractionCandidate.create(
                job_id=job_id,
                kind="bug",
                confidence=bug_confidence,
                data={
                    "title": message.split("\n")[0][:200],
                    "fix_commit": commit_sha,
                    "author": author_name,
                },
                source_commit=commit_sha,
                dedup_key=self._make_dedup_key("bug", commit_sha),
            ))

        # Extract preferences
        pref_confidence = self._check_keywords(message_lower, PREFERENCE_KEYWORDS)
        if pref_confidence > 0:
            candidates.append(ExtractionCandidate.create(
                job_id=job_id,
                kind="preference",
                confidence=pref_confidence,
                data={
                    "key": message.split("\n")[0][:100],
                    "value": message,
                    "author": author_name,
                },
                source_commit=commit_sha,
                dedup_key=self._make_dedup_key("preference", commit_sha),
            ))

        return candidates

    def extract_from_code_comments(
        self,
        job_id: UUID,
        file_path: str,
        content: str,
    ) -> list[ExtractionCandidate]:
        """Extract candidates from code comments."""
        candidates = []

        for i, line in enumerate(content.split("\n"), 1):
            # TODO/FIXME → potential bugs
            match = TODO_PATTERN.search(line) or FIXME_PATTERN.search(line)
            if match:
                candidates.append(ExtractionCandidate.create(
                    job_id=job_id,
                    kind="bug",
                    confidence=0.5,
                    data={
                        "title": f"TODO/FIXME in {file_path}:{i}",
                        "description": match.group(1).strip(),
                    },
                    source_file=file_path,
                    dedup_key=self._make_dedup_key("bug", f"{file_path}:{i}"),
                ))

            # HACK → potential technical debt
            match = HACK_PATTERN.search(line)
            if match:
                candidates.append(ExtractionCandidate.create(
                    job_id=job_id,
                    kind="bug",
                    confidence=0.6,
                    data={
                        "title": f"HACK in {file_path}:{i}",
                        "description": match.group(1).strip(),
                    },
                    source_file=file_path,
                    dedup_key=self._make_dedup_key("bug", f"{file_path}:{i}:hack"),
                ))

            # NOTE/IMPORTANT → potential decisions
            match = NOTE_PATTERN.search(line) or IMPORTANT_PATTERN.search(line)
            if match:
                candidates.append(ExtractionCandidate.create(
                    job_id=job_id,
                    kind="decision",
                    confidence=0.5,
                    data={
                        "title": f"Note in {file_path}:{i}",
                        "rationale": match.group(1).strip(),
                    },
                    source_file=file_path,
                    dedup_key=self._make_dedup_key("decision", f"{file_path}:{i}"),
                ))

        return candidates

    def extract_from_config_change(
        self,
        job_id: UUID,
        file_path: str,
        commit_sha: str,
    ) -> ExtractionCandidate | None:
        """Extract preference from config file changes."""
        config_patterns = [
            r"\.env\.example$", r"pyproject\.toml$", r"\.editorconfig$",
            r"\.prettierrc$", r"\.eslintrc$", r"setup\.cfg$",
            r"\.flake8$", r"\.isort\.cfg$", r"mypy\.ini$",
        ]
        for pattern in config_patterns:
            if re.search(pattern, file_path):
                return ExtractionCandidate.create(
                    project_id=UUID(),  # will be set by caller
                    job_id=job_id,
                    kind="preference",
                    confidence=0.7,
                    data={
                        "key": f"config:{file_path}",
                        "value": f"Config file {file_path} was modified",
                    },
                    source_commit=commit_sha,
                    source_file=file_path,
                    dedup_key=self._make_dedup_key("preference", f"{file_path}:{commit_sha}"),
                )
        return None

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

    def _make_dedup_key(self, kind: str, source: str) -> str:
        """Create a deduplication key."""
        return hashlib.sha256(f"{kind}:{source}".encode()).hexdigest()[:16]
