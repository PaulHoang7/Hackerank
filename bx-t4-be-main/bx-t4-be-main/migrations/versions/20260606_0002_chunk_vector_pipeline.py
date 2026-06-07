"""Add chunk metadata and vector retrieval columns.

Revision ID: 20260606_0002
Revises: 20260605_0001
Create Date: 2026-06-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "20260606_0002"
down_revision: str | None = "20260605_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "video_windows",
        sa.Column("chunk_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.add_column(
        "video_windows",
        sa.Column("index_text", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column("video_windows", sa.Column("clip_storage_key", sa.String(length=1024), nullable=True))
    op.add_column("video_windows", sa.Column("thumbnail_storage_key", sa.String(length=1024), nullable=True))
    op.add_column("video_windows", sa.Column("embedding_vector", Vector(1024), nullable=True))
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_video_windows_embedding_vector
        ON video_windows
        USING hnsw (embedding_vector vector_cosine_ops)
        """
    )
    op.alter_column("video_windows", "chunk_metadata", server_default=None)
    op.alter_column("video_windows", "index_text", server_default=None)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_video_windows_embedding_vector")
    op.drop_column("video_windows", "embedding_vector")
    op.drop_column("video_windows", "thumbnail_storage_key")
    op.drop_column("video_windows", "clip_storage_key")
    op.drop_column("video_windows", "index_text")
    op.drop_column("video_windows", "chunk_metadata")
