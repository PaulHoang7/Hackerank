"""Local multilingual embeddings — the same model the backend/ Streamlit AI uses.

Loads a SentenceTransformer once per process and encodes with L2 normalization
(so cosine == dot product, matching the pgvector hnsw cosine index). Offline and
free: no Gemini key, no per-call cost. Encoding is CPU-bound, so callers should
run :func:`embed_text` via ``asyncio.to_thread``.
"""
from __future__ import annotations

import threading

from app.core.config import get_settings

_model = None
_model_lock = threading.Lock()


def _get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer(get_settings().embedding_model)
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single string into a normalized float vector."""
    vector = _get_model().encode(
        text or "",
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return [float(value) for value in vector.tolist()]
