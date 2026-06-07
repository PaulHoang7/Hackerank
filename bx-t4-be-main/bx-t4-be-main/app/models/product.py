from sqlalchemy import JSON, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import OccurrenceType


class Product(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    product_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)


class ProductOccurrence(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "product_occurrences"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    video_window_id: Mapped[str] = mapped_column(ForeignKey("video_windows.id", ondelete="CASCADE"), index=True)
    occurrence_type: Mapped[OccurrenceType] = mapped_column(
        Enum(OccurrenceType, name="occurrence_type"), nullable=False
    )
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
