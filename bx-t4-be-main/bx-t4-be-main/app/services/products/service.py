import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, ProductOccurrence, VideoWindow
from app.repositories.videos import get_product_occurrences
from app.schemas.video import ProductOccurrenceResponse, ProductResponse


async def products_for_video(session: AsyncSession, video_id: str) -> list[ProductResponse]:
    # Primary: use consolidated Product table (populated by _persist_products)
    rows = await get_product_occurrences(session, video_id)
    if rows:
        grouped: dict[str, tuple[Product, list[ProductOccurrence]]] = {}
        for product, occurrence in rows:
            if product.id not in grouped:
                grouped[product.id] = (product, [])
            grouped[product.id][1].append(occurrence)
        return [build_product_response(product, occs) for product, occs in grouped.values()]

    # Fallback: aggregate product entities directly from video windows
    return await _products_from_detected_entities(session, video_id)


async def _products_from_detected_entities(session: AsyncSession, video_id: str) -> list[ProductResponse]:
    """Build ProductResponse list from detected_entities when Product table is empty."""
    result = await session.scalars(
        select(VideoWindow)
        .where(VideoWindow.video_id == video_id)
        .order_by(VideoWindow.start_time)
    )
    windows = list(result.all())

    # Group product entities by canonical_id (or name if no canonical_id)
    groups: dict[str, dict] = {}  # key → {meta, occurrences}
    for window in windows:
        for entity in (window.detected_entities or []):
            if not isinstance(entity, dict):
                continue
            if entity.get("type") != "product":
                continue
            name = str(entity.get("product_name") or entity.get("name") or "").strip()
            if not name:
                continue
            # Use canonical_id if available, otherwise hash of name for stable grouping
            canonical = str(entity.get("canonical_id") or "")
            key = canonical if canonical else hashlib.md5(name.lower().encode()).hexdigest()[:8]
            if key not in groups:
                groups[key] = {
                    "id": key,
                    "sku": canonical or key,
                    "name": name,
                    "description": entity.get("description"),
                    "brand": entity.get("brand"),
                    "category": entity.get("category"),
                    "occurrences": [],
                }
            groups[key]["occurrences"].append({
                "video_window_id": window.id,
                "timestamp": float(entity.get("timestamp") or window.start_time),
                "confidence": float(entity.get("confidence") or 0.8),
                "occurrence_type": _map_occurrence_type(entity.get("evidence_source", "")),
            })

    return [
        ProductResponse(
            id=g["id"],
            sku=g["sku"],
            name=g["name"],
            description=g.get("description"),
            image_url=None,
            product_metadata={"brand": g.get("brand"), "category": g.get("category")},
            occurrences=[
                ProductOccurrenceResponse(
                    id=f"{g['id']}-{i}",
                    video_window_id=occ["video_window_id"],
                    occurrence_type=occ["occurrence_type"],
                    timestamp=occ["timestamp"],
                    confidence=occ["confidence"],
                )
                for i, occ in enumerate(sorted(g["occurrences"], key=lambda x: x["timestamp"]))
            ],
        )
        for g in groups.values()
    ]


def _map_occurrence_type(evidence_source: str) -> str:
    return "visual"


def build_product_response(product: Product, occurrences: list[ProductOccurrence]) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        image_url=product.image_url,
        product_metadata=product.product_metadata,
        occurrences=[
            ProductOccurrenceResponse(
                id=occurrence.id,
                video_window_id=occurrence.video_window_id,
                occurrence_type=occurrence.occurrence_type,
                timestamp=occurrence.timestamp,
                confidence=occurrence.confidence,
            )
            for occurrence in sorted(occurrences, key=lambda item: item.timestamp)
        ],
    )
