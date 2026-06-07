from pathlib import Path


def detect_scenes(path: Path, duration_seconds: float) -> list[tuple[float, float]]:
    try:
        from scenedetect import ContentDetector, detect

        scenes = detect(str(path), ContentDetector())
        if scenes:
            return [
                (scene[0].get_seconds(), scene[1].get_seconds())
                for scene in scenes
                if scene[1].get_seconds() > scene[0].get_seconds()
            ]
    except Exception:
        # Scene detection is best-effort in the source base; the worker still indexes fixed windows.
        pass

    step = 30.0
    duration = max(duration_seconds or 0, step)
    return [(start, min(start + step, duration)) for start in _frange(0.0, duration, step)]


def _frange(start: float, stop: float, step: float) -> list[float]:
    values: list[float] = []
    value = start
    while value < stop:
        values.append(value)
        value += step
    return values
