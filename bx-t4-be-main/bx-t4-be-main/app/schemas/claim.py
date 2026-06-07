from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Verdict
from app.schemas.common import ORMModel


class ClaimResponse(ORMModel):
    id: str
    video_id: str
    video_window_id: str
    claim_text: str
    timestamp: float
    speaker: str | None
    created_at: datetime


class ClaimVerificationResponse(BaseModel):
    claim_id: str
    claim_text: str
    timestamp: float
    verdict: Verdict
    confidence: float
    explanation: str
    evidence: list[dict]
