from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class ModelUsageLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "model_usage_logs"

    video_id: Mapped[str | None] = mapped_column(
        ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    request_type: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    input_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
