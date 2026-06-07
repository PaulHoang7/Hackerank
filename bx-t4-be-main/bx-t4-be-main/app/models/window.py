from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import EMBEDDING_DIMENSIONS
from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.video import Video


class VideoWindow(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "video_windows"

    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    transcript: Mapped[str] = mapped_column(Text, default="", nullable=False)
    translation: Mapped[str | None] = mapped_column(Text, nullable=True)
    scene_description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ocr_text: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    audio_events: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    detected_entities: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    chunk_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    index_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    clip_storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    thumbnail_storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    energy_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    emotion: Mapped[str | None] = mapped_column(nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    embedding_vector: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=True)

    video: Mapped["Video"] = relationship(back_populates="windows")
