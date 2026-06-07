from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import JobStatus

if TYPE_CHECKING:
    from app.models.video import Video


class ProcessingJob(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "processing_jobs"

    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.queued, nullable=False
    )
    current_step: Mapped[str] = mapped_column(String(128), default="queued", nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    video: Mapped["Video"] = relationship(back_populates="jobs")
