from typing import TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import VideoStatus

if TYPE_CHECKING:
    from app.models.job import ProcessingJob
    from app.models.window import VideoWindow


class Video(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "videos"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    detected_languages: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[VideoStatus] = mapped_column(
        Enum(VideoStatus, name="video_status"), default=VideoStatus.queued, nullable=False
    )

    jobs: Mapped[list["ProcessingJob"]] = relationship(back_populates="video", cascade="all,delete")
    windows: Mapped[list["VideoWindow"]] = relationship(back_populates="video", cascade="all,delete")

    @property
    def latest_job(self) -> "ProcessingJob | None":
        if not self.jobs:
            return None
        return max(self.jobs, key=lambda job: job.created_at)
