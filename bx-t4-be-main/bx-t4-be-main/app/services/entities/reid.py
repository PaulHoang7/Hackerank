"""Phase 4: entity canonicalization + Re-ID.

Takes detected_entities from all VideoWindow records for a video, asks Seed
to deduplicate and canonicalize across windows and languages, then writes
a canonical_id back into each entity dict so QA/retrieval can group by entity
rather than raw name string.

Merges: same product across camera cuts, Vietnamese ↔ English aliases, brand
variations. Works text-only — visual pass already extracted entity descriptions.
"""
from __future__ import annotations

import json
import logging
import re

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import VideoWindow

logger = logging.getLogger(__name__)

REID_SYSTEM = (
    "You are a product catalog resolver for e-commerce livestreams.\n"
    "You are given a list of raw entity mentions extracted per video window. "
    "Many refer to the SAME product under different names, languages (vi/en), "
    "or camera angles — treat those as ONE canonical entity.\n"
    "Produce a JSON object:\n"
    "{\n"
    '  "entities": [\n'
    '    {"canonical_id": "sku_1", "name_vi": "...", "name_en": "...", '
    '"brand": "...", "aliases": [...]}\n'
    "  ],\n"
    '  "mappings": [\n'
    '    {"raw_name": "...", "canonical_id": "sku_1"}\n'
    "  ]\n"
    "}\n"
    "Merge aggressively: do NOT create near-duplicate entities. "
    "Return raw JSON only (no markdown fences)."
)


async def run_entity_reid(session: AsyncSession, video_id: str) -> int:
    """Canonicalize entities across all windows. Returns number of windows updated."""
    settings = get_settings()
    if not settings.seed_omni_api_key:
        return 0

    result = await session.scalars(
        select(VideoWindow).where(VideoWindow.video_id == video_id).order_by(VideoWindow.start_time)
    )
    windows = list(result.all())
    if not windows:
        return 0

    # Collect all raw entity names
    raw_names: set[str] = set()
    window_entity_map: dict[str, list[dict]] = {}
    for w in windows:
        entities = w.detected_entities or []
        window_entity_map[w.id] = entities
        for e in entities:
            if isinstance(e, dict):
                name = e.get("name") or e.get("value") or e.get("text") or ""
                if name:
                    raw_names.add(str(name).strip())

    if not raw_names:
        logger.info("entity_reid_no_entities video_id=%s", video_id)
        return 0

    logger.info("entity_reid_start video_id=%s raw_entities=%d", video_id, len(raw_names))

    # Build a compact list of window-level entity mentions for context
    lines = ["Canonicalize these product entity mentions from a video:"]
    for w in windows:
        entities = window_entity_map.get(w.id, [])
        if not entities:
            continue
        names = [str(e.get("name") or e.get("value") or "") for e in entities if isinstance(e, dict)]
        names = [n for n in names if n]
        if names:
            lines.append(f"  [{w.start_time:.0f}-{w.end_time:.0f}s] {', '.join(names)}")

    payload = {
        "model": settings.seed_omni_model,
        "messages": [
            {"role": "system", "content": REID_SYSTEM},
            {"role": "user", "content": "\n".join(lines)},
        ],
        "max_tokens": 4096,
    }

    try:
        async with httpx.AsyncClient(
            base_url=settings.seed_omni_base_url.rstrip("/"),
            timeout=httpx.Timeout(settings.external_api_timeout_seconds, read=settings.external_api_timeout_seconds),
            headers={"Authorization": f"Bearer {settings.seed_omni_api_key}", "Content-Type": "application/json"},
        ) as client:
            resp = await client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        logger.exception("entity_reid_api_failed video_id=%s", video_id)
        return 0

    # Parse response
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("entity_reid_parse_failed video_id=%s text=%s", video_id, text[:200])
        return 0

    mappings: dict[str, str] = {}
    for item in (data.get("mappings") or []):
        if isinstance(item, dict) and item.get("raw_name") and item.get("canonical_id"):
            mappings[str(item["raw_name"]).strip().lower()] = str(item["canonical_id"])

    if not mappings:
        return 0

    # Apply canonical_id to each entity in every window
    updated = 0
    for w in windows:
        entities = w.detected_entities or []
        changed = False
        new_entities = []
        for e in entities:
            if not isinstance(e, dict):
                new_entities.append(e)
                continue
            name = str(e.get("name") or e.get("value") or "").strip().lower()
            cid = mappings.get(name)
            if cid and e.get("canonical_id") != cid:
                e = {**e, "canonical_id": cid}
                changed = True
            new_entities.append(e)
        if changed:
            w.detected_entities = new_entities
            session.add(w)
            updated += 1

    await session.commit()
    logger.info("entity_reid_done video_id=%s updated_windows=%d mappings=%d", video_id, updated, len(mappings))
    return updated
