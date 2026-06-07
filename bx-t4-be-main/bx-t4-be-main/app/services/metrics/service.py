from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ModelUsageLog, ProcessingJob, Question, Video
from app.models.enums import JobStatus, VideoStatus
from app.schemas.metrics import MetricsOverviewResponse
from app.schemas.video import VideoMetricsResponse


async def overview(session: AsyncSession) -> MetricsOverviewResponse:
    videos_total = await session.scalar(select(func.count(Video.id))) or 0
    videos_indexed = await session.scalar(select(func.count(Video.id)).where(Video.status == VideoStatus.indexed)) or 0
    jobs_processing = (
        await session.scalar(select(func.count(ProcessingJob.id)).where(ProcessingJob.status == JobStatus.processing))
        or 0
    )
    questions_total = await session.scalar(select(func.count(Question.id))) or 0
    qa_estimated_cost_total = float(await session.scalar(select(func.coalesce(func.sum(Question.estimated_cost), 0))) or 0)
    usage_estimated_cost_total = float(await session.scalar(select(func.coalesce(func.sum(ModelUsageLog.estimated_cost), 0))) or 0)
    average_latency_ms = await session.scalar(select(func.coalesce(func.avg(Question.latency_ms), 0))) or 0
    model_calls_total = await session.scalar(select(func.count(ModelUsageLog.id))) or 0
    model_calls_failed = (
        await session.scalar(select(func.count(ModelUsageLog.id)).where(ModelUsageLog.success.is_(False))) or 0
    )
    average_model_latency_ms = await session.scalar(select(func.coalesce(func.avg(ModelUsageLog.latency_ms), 0))) or 0
    return MetricsOverviewResponse(
        videos_total=videos_total,
        videos_indexed=videos_indexed,
        jobs_processing=jobs_processing,
        questions_total=questions_total,
        estimated_cost_total=usage_estimated_cost_total or qa_estimated_cost_total,
        average_latency_ms=float(average_latency_ms),
        model_calls_total=model_calls_total,
        model_calls_failed=model_calls_failed,
        average_model_latency_ms=float(average_model_latency_ms),
    )


async def video_metrics(session: AsyncSession, video_id: str) -> VideoMetricsResponse:
    from app.models import Claim, VideoWindow

    window_count = await session.scalar(select(func.count(VideoWindow.id)).where(VideoWindow.video_id == video_id)) or 0
    claim_count = await session.scalar(select(func.count(Claim.id)).where(Claim.video_id == video_id)) or 0
    question_count = await session.scalar(select(func.count(Question.id)).where(Question.video_id == video_id)) or 0
    estimated_cost = float(
        await session.scalar(
            select(func.coalesce(func.sum(Question.estimated_cost), 0)).where(Question.video_id == video_id)
        )
        or 0
    )
    usage_estimated_cost = float(
        await session.scalar(
            select(func.coalesce(func.sum(ModelUsageLog.estimated_cost), 0)).where(ModelUsageLog.video_id == video_id)
        )
        or 0
    )
    model_call_count = await session.scalar(select(func.count(ModelUsageLog.id)).where(ModelUsageLog.video_id == video_id)) or 0
    failed_model_call_count = (
        await session.scalar(
            select(func.count(ModelUsageLog.id)).where(ModelUsageLog.video_id == video_id, ModelUsageLog.success.is_(False))
        )
        or 0
    )
    average_model_latency_ms = (
        await session.scalar(
            select(func.coalesce(func.avg(ModelUsageLog.latency_ms), 0)).where(ModelUsageLog.video_id == video_id)
        )
        or 0
    )
    return VideoMetricsResponse(
        video_id=video_id,
        window_count=window_count,
        claim_count=claim_count,
        question_count=question_count,
        estimated_cost=usage_estimated_cost or estimated_cost,
        model_call_count=model_call_count,
        failed_model_call_count=failed_model_call_count,
        average_model_latency_ms=float(average_model_latency_ms),
    )
