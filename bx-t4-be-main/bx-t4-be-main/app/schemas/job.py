from datetime import datetime

from app.models.enums import JobStatus
from app.schemas.common import ORMModel


class JobResponse(ORMModel):
    id: str
    video_id: str
    status: JobStatus
    current_step: str
    progress_percent: int
    error_message: str | None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
