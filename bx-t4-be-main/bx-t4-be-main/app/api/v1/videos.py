import asyncio
import logging
import shutil

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_storage
from app.core.exceptions import AppError
from app.core.security import build_storage_key, sanitize_filename
from app.models import ProcessingJob, Video
from app.models.enums import JobStatus, VideoStatus
from app.repositories import videos as video_repo
from app.schemas.claim import ClaimResponse
from app.schemas.video import (
    ImportUrlRequest,
    ProductResponse,
    TimelineWindow,
    UploadResponse,
    VideoMetricsResponse,
    VideoResponse,
)
from app.services.metrics.service import video_metrics
from app.services.products import products_for_video
from app.services.storage import StorageService
from app.services.video.language import english_translation, source_transcript
from app.services.video.url_import import import_public_video_url
from app.services.video.validation import validate_upload
from app.workers.actors import process_video

router = APIRouter(prefix="/videos", tags=["videos"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    storage: StorageService = Depends(get_storage),
) -> UploadResponse:
    file_size = await validate_upload(file)
    video = Video(
        title=sanitize_filename(file.filename or "video"),
        original_filename=file.filename or "video",
        storage_key="pending",
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        status=VideoStatus.queued,
        detected_languages=[],
    )
    session.add(video)
    await session.flush()

    storage_key = build_storage_key(video.id, file.filename or "video")
    # Stream the spooled upload straight to storage — no full-file copy in RAM.
    file.file.seek(0)
    storage.upload_fileobj(storage_key, file.file, file_size, video.content_type)
    video.storage_key = storage_key
    logger.info("upload_received video_id=%s filename=%s size=%s", video.id, video.original_filename, file_size)
    return await _queue_video(session, video)


@router.post("/import-url", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def import_video_url(
    payload: ImportUrlRequest,
    session: AsyncSession = Depends(get_session),
    storage: StorageService = Depends(get_storage),
) -> UploadResponse:
    imported = await asyncio.to_thread(import_public_video_url, payload.url)
    display_name = sanitize_filename(payload.title or imported.filename)
    video = Video(
        title=display_name,
        original_filename=imported.filename,
        storage_key="pending",
        content_type=imported.content_type,
        file_size=imported.file_size,
        status=VideoStatus.queued,
        detected_languages=[],
    )
    session.add(video)
    await session.flush()

    try:
        storage_key = build_storage_key(video.id, imported.filename)
        storage.upload_path(storage_key, imported.path, imported.content_type)
        video.storage_key = storage_key
        logger.info("url_import_received video_id=%s filename=%s size=%s", video.id, video.original_filename, imported.file_size)
        return await _queue_video(session, video)
    finally:
        shutil.rmtree(imported.path.parent, ignore_errors=True)


@router.get("", response_model=list[VideoResponse])
async def list_videos(session: AsyncSession = Depends(get_session)) -> list[Video]:
    return await video_repo.list_videos(session)


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str, session: AsyncSession = Depends(get_session)) -> Video:
    video = await video_repo.get_video(session, video_id)
    if not video:
        raise AppError("VIDEO_NOT_FOUND", "Video not found", status.HTTP_404_NOT_FOUND)
    return video


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: str,
    session: AsyncSession = Depends(get_session),
    storage: StorageService = Depends(get_storage),
) -> None:
    video = await video_repo.get_video(session, video_id)
    if not video:
        raise AppError("VIDEO_NOT_FOUND", "Video not found", status.HTTP_404_NOT_FOUND)
    storage_key = video.storage_key
    await video_repo.delete_video(session, video_id)
    await session.commit()
    storage.delete_file(storage_key)


@router.get("/{video_id}/timeline", response_model=list[TimelineWindow])
async def get_timeline(video_id: str, session: AsyncSession = Depends(get_session)) -> list[TimelineWindow]:
    await _require_video(session, video_id)
    windows = await video_repo.get_timeline(session, video_id)
    return [
        TimelineWindow.model_validate(window).model_copy(
            update={
                "transcript": source_transcript(window),
                "translation": english_translation(window),
            }
        )
        for window in windows
    ]


@router.get("/{video_id}/transcript")
async def get_transcript(video_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    await _require_video(session, video_id)
    windows = await video_repo.get_timeline(session, video_id)
    rows: list[dict] = []
    for window in windows:
        speech_segments = window.chunk_metadata.get("speech_segments") if isinstance(window.chunk_metadata, dict) else None
        if isinstance(speech_segments, list) and speech_segments:
            for segment in speech_segments:
                if not isinstance(segment, dict):
                    continue
                text = str(segment.get("text") or "").strip()
                if not text:
                    continue
                rows.append(
                    {
                        "start_time": float(segment.get("start_time") or segment.get("timestamp") or window.start_time),
                        "end_time": float(segment.get("end_time") or window.end_time),
                        "text": text,
                        "speaker": segment.get("speaker"),
                        "language": segment.get("language"),
                        "translation": segment.get("translation"),
                    }
                )
            continue
        rows.append(
            {
                "start_time": window.start_time,
                "end_time": window.end_time,
                "text": window.transcript,
                "speaker": None,
                "language": window.chunk_metadata.get("language") if isinstance(window.chunk_metadata, dict) else None,
                "translation": window.translation,
            }
        )
    return {
        "video_id": video_id,
        "transcript": rows,
    }


@router.get("/{video_id}/products", response_model=list[ProductResponse])
async def get_products(video_id: str, session: AsyncSession = Depends(get_session)) -> list[ProductResponse]:
    await _require_video(session, video_id)
    return await products_for_video(session, video_id)


@router.get("/{video_id}/claims", response_model=list[ClaimResponse])
async def get_claims(video_id: str, session: AsyncSession = Depends(get_session)) -> list:
    await _require_video(session, video_id)
    return await video_repo.get_claims(session, video_id)


@router.get("/{video_id}/metrics", response_model=VideoMetricsResponse)
async def get_video_metrics(video_id: str, session: AsyncSession = Depends(get_session)) -> VideoMetricsResponse:
    await _require_video(session, video_id)
    return await video_metrics(session, video_id)


async def _require_video(session: AsyncSession, video_id: str) -> Video:
    video = await video_repo.get_video(session, video_id)
    if not video:
        raise AppError("VIDEO_NOT_FOUND", "Video not found", status.HTTP_404_NOT_FOUND)
    return video


async def _queue_video(session: AsyncSession, video: Video) -> UploadResponse:
    job = ProcessingJob(
        video_id=video.id,
        status=JobStatus.queued,
        current_step="queued",
        progress_percent=0,
    )
    session.add(job)
    await session.commit()
    process_video.send(video.id, job.id)
    logger.info("video_job_queued video_id=%s job_id=%s", video.id, job.id)
    return UploadResponse(video_id=video.id, job_id=job.id, status=job.status.value)
