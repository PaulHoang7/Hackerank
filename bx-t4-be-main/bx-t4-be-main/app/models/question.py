from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class Question(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "questions"

    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[int] = mapped_column(default=0, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)


class QuestionEvidence(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "question_evidence"

    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    video_window_id: Mapped[str] = mapped_column(ForeignKey("video_windows.id", ondelete="CASCADE"))
    evidence_frame_id: Mapped[str | None] = mapped_column(
        ForeignKey("evidence_frames.id", ondelete="SET NULL"), nullable=True
    )
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
