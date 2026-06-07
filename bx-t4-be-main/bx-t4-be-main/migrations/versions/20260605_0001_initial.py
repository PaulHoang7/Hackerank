"""Initial schema.

Revision ID: 20260605_0001
Revises:
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260605_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    video_status = sa.Enum("queued", "processing", "indexed", "failed", "deleted", name="video_status")
    job_status = sa.Enum("queued", "processing", "completed", "failed", name="job_status")
    occurrence_type = sa.Enum("visual", "spoken", "ocr", name="occurrence_type")
    verdict = sa.Enum("consistent", "inconsistent", "unclear", name="verdict")
    op.create_table(
        "videos",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("detected_languages", sa.JSON(), nullable=False),
        sa.Column("status", video_status, nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_table(
        "products",
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=1024), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )
    op.create_table(
        "processing_jobs",
        sa.Column("video_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("current_step", sa.String(length=128), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_processing_jobs_video_id"), "processing_jobs", ["video_id"])
    op.create_table(
        "video_windows",
        sa.Column("video_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("translation", sa.Text(), nullable=True),
        sa.Column("scene_description", sa.Text(), nullable=False),
        sa.Column("ocr_text", sa.JSON(), nullable=False),
        sa.Column("audio_events", sa.JSON(), nullable=False),
        sa.Column("detected_entities", sa.JSON(), nullable=False),
        sa.Column("energy_score", sa.Float(), nullable=False),
        sa.Column("emotion", sa.String(), nullable=True),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_video_windows_video_id"), "video_windows", ["video_id"])
    op.create_table(
        "claims",
        sa.Column("video_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("video_window_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("speaker", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_window_id"], ["video_windows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_claims_video_id"), "claims", ["video_id"])
    op.create_index(op.f("ix_claims_video_window_id"), "claims", ["video_window_id"])
    op.create_table(
        "evidence_frames",
        sa.Column("video_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("video_window_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_window_id"], ["video_windows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidence_frames_video_id"), "evidence_frames", ["video_id"])
    op.create_index(op.f("ix_evidence_frames_video_window_id"), "evidence_frames", ["video_window_id"])
    op.create_table(
        "product_occurrences",
        sa.Column("product_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("video_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("video_window_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("occurrence_type", occurrence_type, nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_window_id"], ["video_windows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_occurrences_video_id"), "product_occurrences", ["video_id"])
    op.create_index(op.f("ix_product_occurrences_video_window_id"), "product_occurrences", ["video_window_id"])
    op.create_table(
        "questions",
        sa.Column("video_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questions_video_id"), "questions", ["video_id"])
    op.create_table(
        "claim_verifications",
        sa.Column("claim_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("verdict", verdict, nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_frame_ids", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_claim_verifications_claim_id"), "claim_verifications", ["claim_id"])
    op.create_table(
        "question_evidence",
        sa.Column("question_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("video_window_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("evidence_frame_id", sa.Uuid(as_uuid=False), nullable=True),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["evidence_frame_id"], ["evidence_frames.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_window_id"], ["video_windows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "model_usage_logs",
        sa.Column("video_id", sa.Uuid(as_uuid=False), nullable=True),
        sa.Column("request_type", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_units", sa.Integer(), nullable=False),
        sa.Column("output_units", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_model_usage_logs_video_id"), "model_usage_logs", ["video_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_model_usage_logs_video_id"), table_name="model_usage_logs")
    op.drop_table("model_usage_logs")
    op.drop_table("question_evidence")
    op.drop_index(op.f("ix_claim_verifications_claim_id"), table_name="claim_verifications")
    op.drop_table("claim_verifications")
    op.drop_index(op.f("ix_questions_video_id"), table_name="questions")
    op.drop_table("questions")
    op.drop_index(op.f("ix_product_occurrences_video_window_id"), table_name="product_occurrences")
    op.drop_index(op.f("ix_product_occurrences_video_id"), table_name="product_occurrences")
    op.drop_table("product_occurrences")
    op.drop_index(op.f("ix_evidence_frames_video_window_id"), table_name="evidence_frames")
    op.drop_index(op.f("ix_evidence_frames_video_id"), table_name="evidence_frames")
    op.drop_table("evidence_frames")
    op.drop_index(op.f("ix_claims_video_window_id"), table_name="claims")
    op.drop_index(op.f("ix_claims_video_id"), table_name="claims")
    op.drop_table("claims")
    op.drop_index(op.f("ix_video_windows_video_id"), table_name="video_windows")
    op.drop_table("video_windows")
    op.drop_index(op.f("ix_processing_jobs_video_id"), table_name="processing_jobs")
    op.drop_table("processing_jobs")
    op.drop_table("products")
    op.drop_table("videos")
    for enum_name in ("verdict", "occurrence_type", "job_status", "video_status"):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
