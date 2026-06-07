from sqlalchemy import JSON, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import Verdict


class Claim(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "claims"

    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    video_window_id: Mapped[str] = mapped_column(ForeignKey("video_windows.id", ondelete="CASCADE"), index=True)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)
    speaker: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ClaimVerification(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "claim_verifications"

    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True)
    verdict: Mapped[Verdict] = mapped_column(Enum(Verdict, name="verdict"), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_frame_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
