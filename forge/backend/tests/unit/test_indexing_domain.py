"""Tests for indexing domain model."""

from uuid import uuid4

from forge.domain.indexing.entities.extraction_candidate import ExtractionCandidate
from forge.domain.indexing.entities.file_index import FileIndex
from forge.domain.indexing.entities.index_job import IndexJob
from forge.domain.indexing.value_objects.index_type import IndexType
from forge.domain.indexing.value_objects.job_status import JobStatus


class TestIndexJob:
    def test_create(self):
        job = IndexJob.create(
            project_id=uuid4(),
            type=IndexType.FULL,
        )
        assert job.status == JobStatus.PENDING
        assert job.type == IndexType.FULL
        assert job.is_resumable is False

    def test_start(self):
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        job.start()
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None

    def test_complete(self):
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        job.start()
        job.complete(result={"files": 10}, state_hash="abc123")
        assert job.status == JobStatus.COMPLETED
        assert job.result == {"files": 10}
        assert job.state_hash == "abc123"
        assert job.duration_seconds is not None

    def test_fail(self):
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        job.start()
        job.fail("Something went wrong", phase="parse")
        assert job.status == JobStatus.FAILED
        assert len(job.error_log) == 1
        assert job.error_log[0]["error"] == "Something went wrong"
        assert job.error_log[0]["phase"] == "parse"

    def test_cancel(self):
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        job.start()
        job.cancel()
        assert job.status == JobStatus.CANCELLED

    def test_update_progress(self):
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        job.update_progress("parse", files_done=50, files_total=100)
        assert job.progress["current_phase"] == "parse"
        assert job.progress["files_done"] == 50
        assert job.progress["files_total"] == 100

    def test_save_checkpoint(self):
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        job.save_checkpoint({"last_commit_sha": "abc123", "phase": "parse"})
        assert job.checkpoint["last_commit_sha"] == "abc123"

    def test_log_error(self):
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        job.log_error("src/main.py", "Syntax error", phase="parse")
        assert len(job.error_log) == 1
        assert job.error_log[0]["file"] == "src/main.py"

    def test_is_resumable(self):
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        job.start()
        job.fail("error", phase="parse")
        job.save_checkpoint({"last_commit_sha": "abc", "phase": "parse"})
        assert job.is_resumable is True

    def test_is_not_resumable_without_checkpoint(self):
        job = IndexJob.create(project_id=uuid4(), type=IndexType.FULL)
        job.start()
        job.fail("error")
        assert job.is_resumable is False


class TestFileIndex:
    def test_create(self):
        fi = FileIndex.create(
            project_id=uuid4(),
            file_path="src/main.py",
            content_hash="abc123",
            language="python",
        )
        assert fi.file_path == "src/main.py"
        assert fi.content_hash == "abc123"
        assert fi.language == "python"

    def test_needs_reindex(self):
        fi = FileIndex.create(
            project_id=uuid4(),
            file_path="src/main.py",
            content_hash="abc123",
        )
        assert fi.needs_reindex("def456") is True
        assert fi.needs_reindex("abc123") is False


class TestExtractionCandidate:
    def test_create(self):
        candidate = ExtractionCandidate.create(
            job_id=uuid4(),
            kind="decision",
            confidence=0.8,
            data={"title": "Use FastAPI"},
        )
        assert candidate.kind == "decision"
        assert candidate.confidence == 0.8
        assert candidate.status == "suggested"

    def test_auto_acceptable(self):
        candidate = ExtractionCandidate.create(job_id=uuid4(), kind="decision", confidence=0.9)
        assert candidate.is_auto_acceptable is True
        assert candidate.is_reviewable is False
        assert candidate.is_discardable is False

    def test_reviewable(self):
        candidate = ExtractionCandidate.create(job_id=uuid4(), kind="decision", confidence=0.6)
        assert candidate.is_auto_acceptable is False
        assert candidate.is_reviewable is True
        assert candidate.is_discardable is False

    def test_discardable(self):
        candidate = ExtractionCandidate.create(job_id=uuid4(), kind="decision", confidence=0.3)
        assert candidate.is_auto_acceptable is False
        assert candidate.is_reviewable is False
        assert candidate.is_discardable is True

    def test_accept(self):
        candidate = ExtractionCandidate.create(job_id=uuid4(), kind="decision", confidence=0.8)
        candidate.accept()
        assert candidate.status == "accepted"
        assert candidate.reviewed_at is not None

    def test_reject(self):
        candidate = ExtractionCandidate.create(job_id=uuid4(), kind="decision", confidence=0.6)
        candidate.reject()
        assert candidate.status == "rejected"

    def test_mark_duplicate(self):
        candidate = ExtractionCandidate.create(job_id=uuid4(), kind="decision", confidence=0.8)
        candidate.mark_duplicate()
        assert candidate.status == "duplicate"
