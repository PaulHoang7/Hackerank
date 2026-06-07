from dataclasses import dataclass

from app.models import EvidenceFrame, VideoWindow


@dataclass(frozen=True)
class ValidatedEvidence:
    window: VideoWindow
    frame: EvidenceFrame
    timestamp: float
    rationale: str


def validate_question_evidence(
    evidence_items: list[dict],
    windows: list[VideoWindow],
    frames_by_window_id: dict[str, EvidenceFrame | None],
) -> list[ValidatedEvidence]:
    window_by_id = {window.id: window for window in windows}
    validated: list[ValidatedEvidence] = []

    for item in evidence_items:
        window_id = item.get("video_window_id")
        window = window_by_id.get(window_id)
        if not window:
            continue

        timestamp = float(item.get("timestamp", window.start_time))
        if timestamp < window.start_time or timestamp > window.end_time:
            continue

        frame = frames_by_window_id.get(window.id)
        if not frame:
            continue

        rationale = str(item.get("rationale") or "Selected as supporting evidence.")
        validated.append(ValidatedEvidence(window=window, frame=frame, timestamp=timestamp, rationale=rationale))

    return validated
