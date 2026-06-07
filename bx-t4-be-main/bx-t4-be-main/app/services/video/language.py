from app.models import VideoWindow


def source_transcript(window: VideoWindow) -> str:
    segments = _speech_segments(window)
    text = " ".join(str(segment.get("text") or "").strip() for segment in segments if segment.get("text")).strip()
    return text or window.transcript


def english_translation(window: VideoWindow) -> str | None:
    segments = _speech_segments(window)
    text = " ".join(
        str(segment.get("translation") or "").strip()
        for segment in segments
        if segment.get("translation")
    ).strip()
    return text or window.translation


def _speech_segments(window: VideoWindow) -> list[dict]:
    if not isinstance(window.chunk_metadata, dict):
        return []
    segments = window.chunk_metadata.get("speech_segments")
    if not isinstance(segments, list):
        return []
    return [segment for segment in segments if isinstance(segment, dict)]
