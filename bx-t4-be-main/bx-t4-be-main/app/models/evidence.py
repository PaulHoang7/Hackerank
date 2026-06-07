from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class EvidenceFrame(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "evidence_frames"

    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    video_window_id: Mapped[str] = mapped_column(ForeignKey("video_windows.id", ondelete="CASCADE"), index=True)
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
