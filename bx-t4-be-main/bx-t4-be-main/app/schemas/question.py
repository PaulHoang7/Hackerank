from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class QuestionEvidenceResponse(BaseModel):
    timestamp: float
    start_time: float
    end_time: float
    thumbnail_url: str | None
    clip_url: str | None = None
    transcript: str
    translation: str | None = None
    visual_description: str
    rationale: str


class QuestionResponse(ORMModel):
    id: str
    video_id: str
    question: str
    answer: str
    latency_ms: int
    estimated_cost: float
    created_at: datetime
    evidence: list[QuestionEvidenceResponse] = []
