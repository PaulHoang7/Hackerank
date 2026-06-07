def build_overlapping_chunks(
    duration_seconds: float,
    *,
    chunk_seconds: float = 30.0,
    overlap_seconds: float = 5.0,
    max_chunks: int = 240,
) -> list[tuple[float, float]]:
    duration = max(0.0, duration_seconds or 0.0)
    chunk = max(1.0, chunk_seconds)
    overlap = max(0.0, min(overlap_seconds, chunk - 0.1))
    stride = chunk - overlap

    if duration <= chunk:
        return [(0.0, round(duration if duration > 0 else chunk, 3))]

    windows: list[tuple[float, float]] = []
    start = 0.0
    while start < duration and len(windows) < max_chunks:
        end = min(start + chunk, duration)
        if end - start >= 1.0:
            windows.append((round(start, 3), round(end, 3)))
        if end >= duration:
            break
        start += stride

    return windows or [(0.0, round(max(duration, chunk), 3))]
