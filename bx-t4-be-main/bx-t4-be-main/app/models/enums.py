from enum import StrEnum


class VideoStatus(StrEnum):
    queued = "queued"
    processing = "processing"
    indexed = "indexed"
    failed = "failed"
    deleted = "deleted"


class JobStatus(StrEnum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Verdict(StrEnum):
    consistent = "consistent"
    inconsistent = "inconsistent"
    unclear = "unclear"


class OccurrenceType(StrEnum):
    visual = "visual"
    spoken = "spoken"
    ocr = "ocr"
