"""initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── projects ────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("stack", sa.JSON(), nullable=True),
        sa.Column("goals", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("repository_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # ── architecture_decisions ──────────────────────────────
    op.create_table(
        "architecture_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), server_default=""),
        sa.Column("alternatives", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(50), server_default="accepted"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── bugs ────────────────────────────────────────────────
    op.create_table(
        "bugs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("root_cause", sa.Text(), server_default=""),
        sa.Column("solution", sa.Text(), server_default=""),
        sa.Column("affected_files", sa.JSON(), nullable=True),
        sa.Column("severity", sa.String(50), server_default="medium"),
        sa.Column("resolved", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── code_entries ────────────────────────────────────────
    op.create_table(
        "code_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("entry_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), server_default=""),
        sa.Column("language", sa.String(50), server_default=""),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── commits ─────────────────────────────────────────────
    op.create_table(
        "commits",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("sha", sa.String(40), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("author", sa.String(255), server_default=""),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("files_changed", sa.JSON(), nullable=True),
        sa.Column("classification", sa.String(50), server_default="other"),
        sa.Column("summary", sa.Text(), server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── developer_preferences ───────────────────────────────
    op.create_table(
        "developer_preferences",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0.5"),
        sa.Column("evidence_count", sa.Integer(), server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # ── analysis_reports ────────────────────────────────────
    op.create_table(
        "analysis_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False, index=True),
        sa.Column("pr_number", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(500), server_default=""),
        sa.Column("summary", sa.Text(), server_default=""),
        sa.Column("change_set", sa.JSON(), nullable=True),
        sa.Column("dependency_impact", sa.JSON(), nullable=True),
        sa.Column("historical_context", sa.JSON(), nullable=True),
        sa.Column("risk_assessment", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── extraction_candidates ───────────────────────────────
    op.create_table(
        "extraction_candidates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), nullable=False, index=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="suggested"),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("source_commit", sa.String(40), server_default=""),
        sa.Column("source_file", sa.Text(), server_default=""),
        sa.Column("dedup_key", sa.String(64), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── file_indices ────────────────────────────────────────
    op.create_table(
        "file_indices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False, index=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("language", sa.String(50), server_default=""),
        sa.Column("last_indexed_commit", sa.String(40), server_default=""),
        sa.Column("parsed_at", sa.DateTime(), nullable=False),
        sa.Column("index_job_id", sa.String(36), nullable=True),
    )

    # ── index_jobs ──────────────────────────────────────────
    op.create_table(
        "index_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False, index=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("progress", sa.JSON(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_log", sa.JSON(), nullable=True),
        sa.Column("checkpoint", sa.JSON(), nullable=True),
        sa.Column("state_hash", sa.String(64), server_default=""),
        sa.Column("created_by", sa.String(20), server_default="api"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("index_jobs")
    op.drop_table("file_indices")
    op.drop_table("extraction_candidates")
    op.drop_table("analysis_reports")
    op.drop_table("developer_preferences")
    op.drop_table("commits")
    op.drop_table("code_entries")
    op.drop_table("bugs")
    op.drop_table("architecture_decisions")
    op.drop_table("projects")
