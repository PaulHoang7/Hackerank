def normalize_windows(scenes: list[tuple[float, float]], duration: float, max_windows: int = 12) -> list[tuple[float, float]]:
    if not scenes:
        scenes = [(0.0, max(duration, 30.0))]

    normalized: list[tuple[float, float]] = []
    for start, end in scenes[:max_windows]:
        if end - start < 3:
            continue
        normalized.append((round(start, 3), round(end, 3)))

    return normalized or [(0.0, max(duration, 30.0))]
