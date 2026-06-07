from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProcessingJob


async def get_job(session: AsyncSession, job_id: str) -> ProcessingJob | None:
    return await session.get(ProcessingJob, job_id)
