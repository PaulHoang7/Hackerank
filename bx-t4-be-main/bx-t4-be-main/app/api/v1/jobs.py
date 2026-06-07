from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.core.exceptions import AppError
from app.repositories.jobs import get_job
from app.schemas.job import JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobResponse)
async def job_detail(job_id: str, session: AsyncSession = Depends(get_session)) -> JobResponse:
    job = await get_job(session, job_id)
    if not job:
        raise AppError("JOB_NOT_FOUND", "Processing job not found", status.HTTP_404_NOT_FOUND)
    return JobResponse.model_validate(job)
