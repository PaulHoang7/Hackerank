from datetime import datetime

from pydantic import BaseModel

from app.models.enums import OccurrenceType, VideoStatus
from app.schemas.common import ORMModel
from app.schemas.job import JobResponse


class UploadResponse(BaseModel):
    video_id: str
    job_id: str
    status: str


class ImportUrlRequest(BaseModel):
    url: str
    title: str | None = None


class VideoResponse(ORMModel):
    id: str
    title: str
    original_filename: str
    storage_key: str
    content_type: str
    file_size: int
    duration_seconds: float | None
    detected_languages: list[str]
    status: VideoStatus
    latest_job: JobResponse | None = None
    created_at: datetime
    updated_at: datetime


class TimelineWindow(ORMModel):
    id: str
    start_time: float
    end_time: float
    transcript: str
    translation: str | None
    scene_description: str
    ocr_text: list[dict]
    audio_events: list[dict]
    detected_entities: list[dict]
    chunk_metadata: dict
    index_text: str
    clip_storage_key: str | None
    thumbnail_storage_key: str | None
    energy_score: float
    emotion: str | None


class EvidenceFrameResponse(ORMModel):
    id: str
    timestamp: float
    storage_key: str
    description: str
    thumbnail_url: str | None = None


class ProductOccurrenceResponse(ORMModel):
    id: str
    video_window_id: str
    occurrence_type: OccurrenceType
    timestamp: float
    confidence: float


class ProductResponse(BaseModel):
    id: str
    sku: str
    name: str
    description: str | None
    image_url: str | None
    product_metadata: dict
    occurrences: list[ProductOccurrenceResponse] = []


class VideoMetricsResponse(BaseModel):
    video_id: str
    window_count: int
    claim_count: int
    question_count: int
    estimated_cost: float
    model_call_count: int
    failed_model_call_count: int
    average_model_latency_ms: float
