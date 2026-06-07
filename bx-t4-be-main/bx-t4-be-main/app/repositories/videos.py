from datetime import UTC, datetime

from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Claim, ProcessingJob, Product, ProductOccurrence, Question, Video, VideoWindow
from app.models.enums import JobStatus, VideoStatus


async def list_videos(session: AsyncSession) -> list[Video]:
    result = await session.scalars(
        select(Video)
        .where(Video.status != VideoStatus.deleted)
        .options(selectinload(Video.jobs))
        .order_by(Video.created_at.desc())
    )
    return list(result.all())


async def get_video(session: AsyncSession, video_id: str) -> Video | None:
    video = await session.scalar(select(Video).where(Video.id == video_id).options(selectinload(Video.jobs)))
    if video and video.status == VideoStatus.deleted:
        return None
    return video


async def get_video_with_windows(session: AsyncSession, video_id: str) -> Video | None:
    stmt: Select[tuple[Video]] = select(Video).where(Video.id == video_id).options(selectinload(Video.windows))
    return await session.scalar(stmt)


async def delete_video(session: AsyncSession, video_id: str) -> None:
    now = datetime.now(UTC)
    await session.execute(
        update(Video)
        .where(Video.id == video_id)
        .values(status=VideoStatus.deleted, updated_at=now)
    )
    await session.execute(
        update(ProcessingJob)
        .where(
            ProcessingJob.video_id == video_id,
            ProcessingJob.status.in_([JobStatus.queued, JobStatus.processing, JobStatus.failed]),
        )
        .values(
            status=JobStatus.failed,
            current_step="deleted",
            error_message="Video was deleted by user",
            completed_at=now,
        )
    )


async def get_timeline(session: AsyncSession, video_id: str) -> list[VideoWindow]:
    result = await session.scalars(
        select(VideoWindow)
        .where(VideoWindow.video_id == video_id)
        .order_by(VideoWindow.start_time, VideoWindow.end_time, VideoWindow.created_at.desc())
    )
    windows_by_time: dict[tuple[float, float], VideoWindow] = {}
    for window in result.all():
        key = (round(window.start_time, 3), round(window.end_time, 3))
        windows_by_time.setdefault(key, window)
    return [windows_by_time[key] for key in sorted(windows_by_time)]


async def get_claims(session: AsyncSession, video_id: str) -> list[Claim]:
    result = await session.scalars(select(Claim).where(Claim.video_id == video_id))
    return list(result.all())


async def get_questions(session: AsyncSession, video_id: str) -> list[Question]:
    result = await session.scalars(select(Question).where(Question.video_id == video_id))
    return list(result.all())


async def get_products(session: AsyncSession, video_id: str) -> list[Product]:
    result = await session.scalars(
        select(Product)
        .join(ProductOccurrence, ProductOccurrence.product_id == Product.id)
        .where(ProductOccurrence.video_id == video_id)
        .distinct()
    )
    return list(result.all())


async def get_product_occurrences(session: AsyncSession, video_id: str) -> list[tuple[Product, ProductOccurrence]]:
    result = await session.execute(
        select(Product, ProductOccurrence)
        .join(ProductOccurrence, ProductOccurrence.product_id == Product.id)
        .where(ProductOccurrence.video_id == video_id)
        .order_by(ProductOccurrence.timestamp)
    )
    return list(result.all())
