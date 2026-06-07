import asyncio
import logging
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from sqlalchemy import delete, select, text

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models import Claim, EvidenceFrame, ProcessingJob, Product, ProductOccurrence, Video, VideoWindow
from app.models.enums import JobStatus, OccurrenceType, VideoStatus
from app.services.ai import get_ai_provider
from app.services.storage import get_storage_service
from app.services.ai.base import VideoWindowInput
from app.services.video.chunks import build_overlapping_chunks
from app.services.audio.asr import run_asr
from app.services.entities.reid import run_entity_reid
from app.services.video.probe import extract_clip, extract_metadata, extract_thumbnail, transcode_proxy
from app.services.usage import estimated_model_cost, log_model_usage

logger = logging.getLogger(__name__)


class VideoDeletedDuringProcessing(Exception):
    pass


async def run_video_pipeline(video_id: str, job_id: str) -> None:
    async with AsyncSessionLocal() as session:
        video = await session.get(Video, video_id)
        job = await session.get(ProcessingJob, job_id)
        if not video or not job:
            return
        lock_key = f"video_pipeline:{job_id}"
        if not await _try_advisory_lock(session, lock_key):
            logger.warning("video_pipeline_duplicate_skipped video_id=%s job_id=%s", video_id, job_id)
            return
        try:
            await _raise_if_deleted(session, video, job)
            if job.status == JobStatus.completed or video.status == VideoStatus.indexed:
                logger.info("video_pipeline_already_completed_skipped video_id=%s job_id=%s", video_id, job_id)
                return
            logger.info("video_pipeline_started video_id=%s job_id=%s", video_id, job_id)
            await _clear_existing_index(session, video)
            await _update_job(session, video, job, "validate_video", 5)
            storage = get_storage_service()
            provider = get_ai_provider()
            with tempfile.TemporaryDirectory() as tmpdir:
                local_video = Path(tmpdir) / video.original_filename
                storage.download_to_path(video.storage_key, local_video)

                await _update_job(session, video, job, "extract_metadata", 15)
                metadata = extract_metadata(local_video)
                video.duration_seconds = metadata["duration_seconds"]
                logger.info("video_metadata_extracted video_id=%s duration=%s", video.id, video.duration_seconds)

                # Auto proxy: downscale the (possibly huge) source once. Everything
                # downstream — playback and per-chunk clip/thumbnail extraction — then
                # runs off the small proxy. Failure is non-fatal: fall back to original.
                await _update_job(session, video, job, "transcode_proxy", 25)
                proxy_path = Path(tmpdir) / f"proxy-{video.id}.mp4"
                try:
                    transcode_proxy(local_video, proxy_path)
                    proxy_key = f"videos/{video.id}/proxy.mp4"
                    storage.upload_path(proxy_key, proxy_path, "video/mp4")
                    old_key = video.storage_key
                    video.storage_key = proxy_key
                    video.content_type = "video/mp4"
                    video.file_size = proxy_path.stat().st_size
                    await session.commit()
                    if old_key and old_key != proxy_key:
                        storage.delete_file(old_key)
                    local_video = proxy_path
                    logger.info(
                        "video_proxy_created video_id=%s proxy_bytes=%s",
                        video.id,
                        proxy_path.stat().st_size,
                    )
                except Exception:
                    logger.exception("video_proxy_failed video_id=%s using_original", video.id)

                await _update_job(session, video, job, "build_chunks", 35)
                settings = get_settings()
                windows = build_overlapping_chunks(
                    video.duration_seconds or 30.0,
                    chunk_seconds=settings.video_chunk_seconds,
                    overlap_seconds=settings.video_chunk_overlap_seconds,
                    max_chunks=settings.video_max_chunks,
                )
                logger.info("video_chunks_built video_id=%s chunks=%s", video.id, len(windows))

                await _update_job(session, video, job, "extract_frames", 40)
                await _persist_windows(session, storage, provider, video, job, local_video, windows, tmpdir)

                await _raise_if_deleted(session, video, job)
                await _update_job(session, video, job, "persist_index", 80)
                await _persist_products(session, provider, video.id)

                # Phase 3: dedicated audio pass — enriches transcript/translation/audio_events/energy
                await _raise_if_deleted(session, video, job)
                await _update_job(session, video, job, "audio_asr", 88)
                try:
                    await run_asr(session, video.id, local_video)
                except Exception:
                    logger.exception("asr_pass_failed_non_fatal video_id=%s", video.id)

                # Phase 4: entity Re-ID — canonical entity IDs across cuts/languages
                await _raise_if_deleted(session, video, job)
                await _update_job(session, video, job, "entity_reid", 94)
                try:
                    await run_entity_reid(session, video.id)
                except Exception:
                    logger.exception("entity_reid_failed_non_fatal video_id=%s", video.id)

                await _raise_if_deleted(session, video, job)
                await _update_job(session, video, job, "finalize_job", 100, completed=True)
                logger.info("video_pipeline_completed video_id=%s job_id=%s", video.id, job.id)
        except VideoDeletedDuringProcessing:
            logger.info("video_pipeline_cancelled_deleted video_id=%s job_id=%s", video_id, job_id)
            return
        except Exception as exc:
            logger.exception("video_pipeline_failed video_id=%s job_id=%s", video_id, job_id)
            await session.refresh(video)
            if video.status != VideoStatus.deleted:
                video.status = VideoStatus.failed
                job.status = JobStatus.failed
                job.error_message = str(exc)
                job.completed_at = datetime.now(UTC)
                await session.commit()
            raise
        finally:
            await _release_advisory_lock(session, lock_key)


async def _update_job(
    session,
    video: Video,
    job: ProcessingJob,
    step: str,
    progress: int,
    completed: bool = False,
) -> None:
    now = datetime.now(UTC)
    job.status = JobStatus.completed if completed else JobStatus.processing
    job.current_step = step
    job.progress_percent = progress
    job.started_at = job.started_at or now
    job.completed_at = now if completed else None
    video.status = VideoStatus.indexed if completed else VideoStatus.processing
    await session.commit()
    logger.info(
        "video_job_step video_id=%s job_id=%s step=%s progress=%s status=%s",
        video.id,
        job.id,
        step,
        progress,
        job.status.value,
    )

async def _clear_existing_index(session, video: Video) -> None:
    await session.execute(delete(VideoWindow).where(VideoWindow.video_id == video.id))
    video.detected_languages = []
    video.duration_seconds = None
    await session.commit()


async def _analyze_chunk(
    provider,
    video_id: str,
    local_video: Path,
    tmpdir: str,
    index: int,
    start: float,
    end: float,
    sem: asyncio.Semaphore,
) -> dict:
    """Do the slow, independent work for one chunk: ffmpeg + Seed + embedding.

    Takes only primitives (NOT the ORM ``video``): touching a session-bound ORM
    attribute here would trigger a lazy reload on the shared AsyncSession from
    multiple coroutines at once ("session is provisioning a new connection").
    Only the serial caller touches the session. ffmpeg runs in a thread.
    """
    async with sem:
        logger.info(
            "video_window_started video_id=%s chunk_index=%s start=%s end=%s",
            video_id, index, start, end,
        )
        thumbnail_path = Path(tmpdir) / f"thumb-{index:03d}.jpg"
        clip_path = Path(tmpdir) / f"clip-{index:03d}.mp4"
        await asyncio.to_thread(extract_thumbnail, local_video, thumbnail_path, start)
        await asyncio.to_thread(extract_clip, local_video, clip_path, start, end)

        analyze_started = perf_counter()
        analysis = await provider.analyze_video_window(
            VideoWindowInput(
                video_id=video_id,
                start_time=start,
                end_time=end,
                local_video_path=local_video,
                thumbnail_path=thumbnail_path,
                clip_path=clip_path,
            )
        )
        analyze_ms = int((perf_counter() - analyze_started) * 1000)

        index_text = _index_text(analysis, start, end)
        embed_started = perf_counter()
        embedding = await provider.generate_embedding(index_text, task_type="RETRIEVAL_DOCUMENT")
        embed_ms = int((perf_counter() - embed_started) * 1000)

        return {
            "index": index,
            "start": start,
            "end": end,
            "analysis": analysis,
            "index_text": index_text,
            "embedding": embedding,
            "thumbnail_path": thumbnail_path,
            "clip_path": clip_path,
            "local_video": local_video,
            "analyze_ms": analyze_ms,
            "embed_ms": embed_ms,
        }


async def _persist_windows(
    session,
    storage,
    provider,
    video: Video,
    job: ProcessingJob,
    local_video: Path,
    windows: list[tuple[float, float]],
    tmpdir: str,
) -> None:
    total = len(windows) or 1
    video_id = video.id  # read once while the session is idle; tasks must not touch ORM
    concurrency = max(1, get_settings().seed_analysis_concurrency)
    sem = asyncio.Semaphore(concurrency)
    tasks = [
        asyncio.create_task(
            _analyze_chunk(provider, video_id, local_video, tmpdir, index, start, end, sem)
        )
        for index, (start, end) in enumerate(windows)
    ]
    logger.info(
        "video_windows_fanout video_id=%s chunks=%s concurrency=%s",
        video.id, total, concurrency,
    )

    completed = 0
    try:
        for finished in asyncio.as_completed(tasks):
            try:
                result = await finished
            except Exception as exc:
                # A single chunk failing must not sink the whole video.
                logger.exception("video_window_failed video_id=%s", video.id)
                await log_model_usage(
                    session,
                    provider,
                    request_type="video_window_analysis",
                    video_id=video.id,
                    latency_ms=0,
                    estimated_cost=estimated_model_cost("video_window_analysis"),
                    success=False,
                    error_message=str(exc),
                    input_units=0,
                )
            else:
                await _raise_if_deleted(session, video)
                await _persist_one_window(session, storage, provider, video, result)

            completed += 1
            job.current_step = f"extract_frames ({completed}/{total})"
            job.progress_percent = 40 + int(completed / total * 38)
            await session.commit()
    except BaseException:
        for task in tasks:
            task.cancel()
        raise


async def _persist_one_window(session, storage, provider, video: Video, result: dict) -> None:
    index = result["index"]
    start = result["start"]
    end = result["end"]
    analysis = result["analysis"]
    thumbnail_path = result["thumbnail_path"]
    clip_path = result["clip_path"]

    await log_model_usage(
        session,
        provider,
        request_type="video_window_analysis",
        video_id=video.id,
        latency_ms=result["analyze_ms"],
        estimated_cost=estimated_model_cost("video_window_analysis"),
        input_units=int(end - start),
        output_units=len(analysis.scene_description) + len(analysis.transcript),
    )

    chunk_metadata = _chunk_metadata(index, start, end, result["local_video"], clip_path)
    chunk_metadata.update(
        {
            "language": analysis.language,
            "speech_segments": analysis.speech_segments,
            "visual_evidence": analysis.visual_evidence,
        }
    )
    if analysis.language and analysis.language not in {"unknown", "mixed"}:
        languages = set(video.detected_languages or [])
        languages.add(analysis.language)
        video.detected_languages = sorted(languages)

    window = VideoWindow(
        video_id=video.id,
        start_time=start,
        end_time=end,
        transcript=analysis.transcript,
        translation=analysis.translation,
        scene_description=analysis.scene_description,
        ocr_text=analysis.ocr_text,
        audio_events=analysis.audio_events,
        detected_entities=analysis.detected_entities,
        chunk_metadata=chunk_metadata,
        index_text=result["index_text"],
        energy_score=analysis.energy_score,
        emotion=analysis.emotion,
    )

    embedding = result["embedding"]
    await log_model_usage(
        session,
        provider,
        request_type="embedding_document",
        video_id=video.id,
        latency_ms=result["embed_ms"],
        estimated_cost=estimated_model_cost("embedding_document"),
        input_units=len(window.index_text),
        output_units=len(embedding),
    )
    window.embedding = embedding
    window.embedding_vector = embedding
    session.add(window)
    await session.flush()

    thumbnail_key = f"thumbnails/{video.id}/{window.id}.jpg"
    clip_key = f"clips/{video.id}/{window.id}.mp4"
    storage.upload_path(thumbnail_key, thumbnail_path, "image/jpeg")
    storage.upload_path(clip_key, clip_path, "video/mp4")
    window.thumbnail_storage_key = thumbnail_key
    window.clip_storage_key = clip_key
    session.add(
        EvidenceFrame(
            video_id=video.id,
            video_window_id=window.id,
            timestamp=start,
            storage_key=thumbnail_key,
            description=analysis.scene_description,
        )
    )

    for claim in analysis.claims:
        session.add(
            Claim(
                video_id=video.id,
                video_window_id=window.id,
                claim_text=claim["claim_text"],
                timestamp=claim["timestamp"],
                speaker=claim.get("speaker"),
            )
        )
    logger.info(
        "video_window_completed video_id=%s chunk_index=%s window_id=%s products=%s claims=%s",
        video.id,
        index,
        window.id,
        len([entity for entity in analysis.detected_entities if isinstance(entity, dict) and entity.get("type") == "product"]),
        len(analysis.claims),
    )


async def _persist_products(session, provider, video_id: str) -> None:
    video = await session.get(Video, video_id)
    if not video or video.status == VideoStatus.deleted:
        raise VideoDeletedDuringProcessing
    result = await session.scalars(
        select(VideoWindow).where(VideoWindow.video_id == video_id).order_by(VideoWindow.start_time)
    )
    windows = [
        {
            "id": window.id,
            "start_time": window.start_time,
            "end_time": window.end_time,
            "transcript": window.transcript,
            "scene_description": window.scene_description,
            "ocr_text": window.ocr_text,
            "audio_events": window.audio_events,
            "detected_entities": window.detected_entities,
        }
        for window in result.all()
    ]
    started = perf_counter()
    try:
        detected_products = await provider.detect_products(video_id, windows)
        await log_model_usage(
            session,
            provider,
            request_type="product_consolidation",
            video_id=video_id,
            latency_ms=int((perf_counter() - started) * 1000),
            estimated_cost=estimated_model_cost("product_consolidation"),
            input_units=len(windows),
            output_units=len(detected_products),
        )
    except Exception as exc:
        await log_model_usage(
            session,
            provider,
            request_type="product_consolidation",
            video_id=video_id,
            latency_ms=int((perf_counter() - started) * 1000),
            estimated_cost=estimated_model_cost("product_consolidation"),
            success=False,
            error_message=str(exc),
            input_units=len(windows),
        )
        raise
    logger.info("video_products_consolidated video_id=%s products=%s", video_id, len(detected_products))
    for detected in detected_products:
        product = await session.scalar(select(Product).where(Product.sku == detected["sku"]))
        if not product:
            product = Product(
                sku=detected["sku"],
                name=detected["name"],
                description=detected["description"],
                image_url=None,
                product_metadata={"source": provider.name, **(detected.get("metadata") or {})},
            )
            session.add(product)
            await session.flush()
        for occurrence in detected.get("occurrences") or [
            {
                "video_window_id": detected["video_window_id"],
                "timestamp": detected["timestamp"],
                "occurrence_type": "visual",
                "confidence": detected["confidence"],
            }
        ]:
            session.add(
                ProductOccurrence(
                    product_id=product.id,
                    video_id=video_id,
                    video_window_id=occurrence["video_window_id"],
                    occurrence_type=_occurrence_type(occurrence.get("occurrence_type")),
                    timestamp=float(occurrence.get("timestamp") or detected["timestamp"]),
                    confidence=float(occurrence.get("confidence") or detected["confidence"]),
                )
            )
    await session.commit()


async def _raise_if_deleted(session, video: Video, job: ProcessingJob | None = None) -> None:
    await session.refresh(video)
    if video.status != VideoStatus.deleted:
        return
    if job:
        job.status = JobStatus.failed
        job.current_step = "deleted"
        job.error_message = "Video was deleted by user"
        job.completed_at = datetime.now(UTC)
        await session.commit()
    raise VideoDeletedDuringProcessing


def _retrieval_text(analysis) -> str:
    return "\n".join(
        [
            analysis.transcript,
            analysis.scene_description,
            " ".join(str(item) for item in analysis.ocr_text),
            " ".join(str(item) for item in analysis.audio_events),
            " ".join(str(item) for item in analysis.detected_entities),
        ]
    ).strip()


def _index_text(analysis, start: float, end: float) -> str:
    product_lines = []
    entity_lines = []
    for entity in analysis.detected_entities:
        if not isinstance(entity, dict):
            continue
        if entity.get("type") == "product":
            product_lines.append(
                " ".join(
                    str(entity.get(key) or "")
                    for key in ("brand", "product_name", "name", "category", "description", "evidence_source")
                )
            )
        elif entity.get("type") in {
            "brand",
            "price",
            "promotion",
            "business_event",
            "action",
            "host",
            "kol",
            "creator",
            "shop",
            "channel",
            "person",
            "platform",
        }:
            product_lines.append(str(entity))
            entity_lines.append(str(entity))
    return "\n".join(
        [
            f"chunk: {start:.3f}-{end:.3f}",
            f"language: {analysis.language or 'unknown'}",
            f"scene: {analysis.scene_description}",
            f"transcript: {analysis.transcript}",
            f"speech_segments: {' '.join(str(item) for item in analysis.speech_segments)}",
            f"visual_evidence: {' '.join(str(item) for item in analysis.visual_evidence)}",
            f"ocr: {' '.join(str(item) for item in analysis.ocr_text)}",
            f"entities: {' '.join(product_lines)}",
            f"people_channels: {' '.join(entity_lines)}",
            f"audio_events: {' '.join(str(item) for item in analysis.audio_events)}",
        ]
    ).strip()


def _chunk_metadata(index: int, start: float, end: float, source_video: Path, clip_path: Path) -> dict:
    return {
        "chunk_index": index,
        "start_time": start,
        "end_time": end,
        "duration_seconds": round(end - start, 3),
        "source_filename": source_video.name,
        "clip_filename": clip_path.name,
        "clip_size_bytes": clip_path.stat().st_size if clip_path.exists() else 0,
    }


def _occurrence_type(value: object) -> OccurrenceType:
    try:
        return OccurrenceType(str(value))
    except ValueError:
        return OccurrenceType.visual


async def _try_advisory_lock(session, lock_key: str) -> bool:
    result = await session.execute(text("select pg_try_advisory_lock(hashtext(:lock_key))"), {"lock_key": lock_key})
    return bool(result.scalar())


async def _release_advisory_lock(session, lock_key: str) -> None:
    await session.execute(text("select pg_advisory_unlock(hashtext(:lock_key))"), {"lock_key": lock_key})
