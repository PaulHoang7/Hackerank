"""Switch embedding_vector to the local model's dimension (1024 -> 384).

The AI layer was unified with backend/ (SentenceTransformer
paraphrase-multilingual-MiniLM-L12-v2, 384-dim) instead of Gemini (1024-dim).
Existing 1024-dim vectors can't be cast, so we drop and recreate the column and
its hnsw index; affected videos must be re-indexed.

Revision ID: 20260607_0003
Revises: 20260606_0002
Create Date: 2026-06-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "20260607_0003"
down_revision: str | None = "20260606_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_DIM = 384
_OLD_DIM = 1024


def _reset_vector_column(dim: int) -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("DROP INDEX IF EXISTS ix_video_windows_embedding_vector")
    op.drop_column("video_windows", "embedding_vector")
    op.add_column("video_windows", sa.Column("embedding_vector", Vector(dim), nullable=True))
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_video_windows_embedding_vector
        ON video_windows
        USING hnsw (embedding_vector vector_cosine_ops)
        """
    )


def upgrade() -> None:
    _reset_vector_column(_NEW_DIM)


def downgrade() -> None:
    _reset_vector_column(_OLD_DIM)
