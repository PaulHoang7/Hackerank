import re
from collections.abc import Iterable
from time import perf_counter

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import VideoWindow
from app.services.ai.base import VideoIntelligenceProvider
from app.services.usage import estimated_model_cost, log_model_usage

TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)


def build_window_context(question: str, windows: Iterable[VideoWindow], limit: int = 8) -> list[dict]:
    windows_list = list(windows)
    ranked = _bm25_rank(question, windows_list)
    selected = ranked[:limit] if ranked else windows_list[:limit]
    return [_window_context(window) for window in selected]


async def retrieve_window_context(
    session: AsyncSession,
    provider: VideoIntelligenceProvider,
    video_id: str,
    question: str,
) -> list[dict]:
    settings = get_settings()
    top_k = settings.retrieval_vector_top_k

    # Load all windows upfront — needed for BM25 corpus
    result = await session.scalars(
        select(VideoWindow).where(VideoWindow.video_id == video_id).order_by(VideoWindow.start_time)
    )
    all_windows = list(result.all())

    vector_candidates = await _vector_candidates(session, provider, video_id, question, top_k)
    bm25_candidates = _bm25_rank(question, all_windows)[:top_k]

    # RRF fusion: score = Σ 1/(60+rank) over both ranked lists
    rrf: dict[str, float] = {}
    for rank, w in enumerate(vector_candidates):
        rrf[w.id] = rrf.get(w.id, 0.0) + 1.0 / (60 + rank)
    for rank, w in enumerate(bm25_candidates):
        rrf[w.id] = rrf.get(w.id, 0.0) + 1.0 / (60 + rank)

    by_id = {w.id: w for w in all_windows}
    merged = [by_id[wid] for wid in sorted(rrf, key=lambda x: rrf[x], reverse=True) if wid in by_id]

    # RRF already produces a well-ranked list via Gemini+BM25 fusion.
    # Skipping the separate Seed rerank call saves 3–5s per QA request.
    top_k = settings.retrieval_rerank_top_k
    contexts = [_window_context(w) for w in merged[:top_k]]
    if not contexts:
        contexts = [_window_context(w) for w in all_windows[:top_k]]
    return contexts


async def _vector_candidates(
    session: AsyncSession,
    provider: VideoIntelligenceProvider,
    video_id: str,
    question: str,
    limit: int,
) -> list[VideoWindow]:
    started = perf_counter()
    try:
        query_embedding = await provider.generate_embedding(question, task_type="RETRIEVAL_QUERY")
        await log_model_usage(
            session,
            provider,
            request_type="embedding_query",
            video_id=video_id,
            latency_ms=int((perf_counter() - started) * 1000),
            estimated_cost=estimated_model_cost("embedding_query"),
            input_units=len(question),
            output_units=len(query_embedding),
        )
    except Exception as exc:
        await log_model_usage(
            session,
            provider,
            request_type="embedding_query",
            video_id=video_id,
            latency_ms=int((perf_counter() - started) * 1000),
            estimated_cost=estimated_model_cost("embedding_query"),
            success=False,
            error_message=str(exc),
            input_units=len(question),
        )
        raise
    distance = VideoWindow.embedding_vector.cosine_distance(query_embedding).label("distance")
    result = await session.execute(
        select(VideoWindow, distance)
        .where(VideoWindow.video_id == video_id, VideoWindow.embedding_vector.is_not(None))
        .order_by(distance)
        .limit(limit)
    )
    return [row[0] for row in result.all()]


def rank_windows(question: str, windows: Iterable[VideoWindow]) -> list[VideoWindow]:
    """BM25 ranking — kept for backward compat; prefer _bm25_rank internally."""
    return _bm25_rank(question, list(windows))


def _bm25_rank(question: str, windows: list[VideoWindow]) -> list[VideoWindow]:
    """Rank windows by BM25Okapi score; returns only windows with score > 0."""
    if not windows:
        return []

    def _window_text(w: VideoWindow) -> str:
        if w.index_text:
            return w.index_text
        return " ".join(filter(None, [
            w.transcript or "",
            w.scene_description or "",
            _stringify_items(w.ocr_text or []),
            _stringify_items(w.audio_events or []),
            _stringify_items(w.detected_entities or []),
        ]))

    corpus = [_tok(_window_text(w)) for w in windows]
    if not any(corpus):
        return list(windows)

    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(_tok(question))
    indexed = sorted(range(len(windows)), key=lambda i: scores[i], reverse=True)
    return [windows[i] for i in indexed if scores[i] > 0]


def _window_context(window: VideoWindow) -> dict:
    return {
        "id": window.id,
        "start_time": window.start_time,
        "end_time": window.end_time,
        "transcript": window.transcript,
        "scene_description": window.scene_description,
        "ocr_text": window.ocr_text,
        "audio_events": window.audio_events,
        "detected_entities": window.detected_entities,
        "chunk_metadata": window.chunk_metadata,
        "index_text": window.index_text,
        "clip_storage_key": window.clip_storage_key,
        "thumbnail_storage_key": window.thumbnail_storage_key,
    }


def _tok(text: str) -> list[str]:
    """Tokenize for BM25 (returns list, handles numbers+units and unicode words)."""
    return re.findall(r"[0-9]+[a-z%]*|[^\W\d_]+", (text or "").lower())


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text)}


def _stringify_items(items: list[dict]) -> str:
    return " ".join(str(value) for item in items for value in item.values())
