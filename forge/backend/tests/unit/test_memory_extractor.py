"""Tests for MemoryExtractor."""
import pytest
from uuid import uuid4

from forge.application.indexing.memory_extractor import MemoryExtractor


class TestMemoryExtractor:
    def setup_method(self):
        self.extractor = MemoryExtractor()

    def test_extract_decision_from_commit(self):
        candidates = self.extractor.extract_from_commit_message(
            job_id=uuid4(),
            commit_sha="abc123",
            message="decided to use FastAPI instead of Flask",
            author_name="dev",
            files_changed=["src/api/routes.py"],
        )
        assert len(candidates) >= 1
        decision = [c for c in candidates if c.kind == "decision"]
        assert len(decision) == 1
        assert decision[0].confidence > 0.5

    def test_extract_bug_fix_from_commit(self):
        candidates = self.extractor.extract_from_commit_message(
            job_id=uuid4(),
            commit_sha="def456",
            message="fix: null pointer in auth module",
            author_name="dev",
            files_changed=["src/auth.py"],
        )
        assert len(candidates) >= 1
        bugs = [c for c in candidates if c.kind == "bug"]
        assert len(bugs) == 1
        assert bugs[0].confidence > 0.5

    def test_extract_preference_from_commit(self):
        candidates = self.extractor.extract_from_commit_message(
            job_id=uuid4(),
            commit_sha="ghi789",
            message="prefer snake_case for Python files",
            author_name="dev",
            files_changed=[],
        )
        assert len(candidates) >= 1
        prefs = [c for c in candidates if c.kind == "preference"]
        assert len(prefs) == 1

    def test_extract_from_code_comments_todo(self):
        candidates = self.extractor.extract_from_code_comments(
            job_id=uuid4(),
            file_path="src/main.py",
            content="# TODO: refactor this\nprint('hello')",
        )
        assert len(candidates) == 1
        assert candidates[0].kind == "bug"
        assert candidates[0].confidence == 0.5

    def test_extract_from_code_comments_fixme(self):
        candidates = self.extractor.extract_from_code_comments(
            job_id=uuid4(),
            file_path="src/main.py",
            content="# FIXME: broken auth check",
        )
        assert len(candidates) == 1
        assert candidates[0].kind == "bug"

    def test_extract_from_code_comments_hack(self):
        candidates = self.extractor.extract_from_code_comments(
            job_id=uuid4(),
            file_path="src/main.py",
            content="# HACK: temporary workaround",
        )
        assert len(candidates) == 1
        assert candidates[0].kind == "bug"
        assert candidates[0].confidence == 0.6

    def test_extract_from_code_comments_note(self):
        candidates = self.extractor.extract_from_code_comments(
            job_id=uuid4(),
            file_path="src/main.py",
            content="# NOTE: this is important",
        )
        assert len(candidates) == 1
        assert candidates[0].kind == "decision"
        assert candidates[0].confidence == 0.5

    def test_no_extraction_from_clean_code(self):
        candidates = self.extractor.extract_from_code_comments(
            job_id=uuid4(),
            file_path="src/main.py",
            content="def hello():\n    return 'world'",
        )
        assert len(candidates) == 0

    def test_dedup_key_is_stable(self):
        c1 = self.extractor.extract_from_commit_message(
            job_id=uuid4(),
            commit_sha="abc123",
            message="fix: bug",
            author_name="dev",
            files_changed=[],
        )
        c2 = self.extractor.extract_from_commit_message(
            job_id=uuid4(),
            commit_sha="abc123",
            message="fix: bug again",
            author_name="dev",
            files_changed=[],
        )
        # Same commit SHA should produce same dedup key
        assert c1[0].dedup_key == c2[0].dedup_key

    def test_confidence_scales_with_keyword_matches(self):
        candidates = self.extractor.extract_from_commit_message(
            job_id=uuid4(),
            commit_sha="abc123",
            message="decided to chose adopt FastAPI for API architecture",
            author_name="dev",
            files_changed=[],
        )
        decision = [c for c in candidates if c.kind == "decision"][0]
        assert decision.confidence >= 0.7
