import tempfile
from pathlib import Path
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models import EvidenceFrame, Question, QuestionEvidence, Video, VideoWindow
from app.schemas.question import QuestionEvidenceResponse, QuestionResponse
from app.services.ai import get_ai_provider
from app.services.ai.base import QuestionAnswer
from app.services.retrieval import retrieve_window_context
from app.services.storage import get_storage_service
from app.services.usage import estimated_model_cost, log_model_usage
from app.services.video.language import english_translation, source_transcript
from app.services.video.probe import extract_thumbnail


async def build_question_response(session: AsyncSession, question: Question) -> QuestionResponse:
    storage = get_storage_service()
    result = await session.execute(
        select(QuestionEvidence, VideoWindow, EvidenceFrame)
        .join(VideoWindow, VideoWindow.id == QuestionEvidence.video_window_id)
        .outerjoin(EvidenceFrame, EvidenceFrame.id == QuestionEvidence.evidence_frame_id)
        .where(QuestionEvidence.question_id == question.id)
        .order_by(QuestionEvidence.timestamp)
    )
    evidence = [
        QuestionEvidenceResponse(
            timestamp=item.timestamp,
            start_time=window.start_time,
            end_time=window.end_time,
            thumbnail_url=storage.get_file_url(frame.storage_key) if frame else None,
            clip_url=storage.get_file_url(window.clip_storage_key) if window.clip_storage_key else None,
            transcript=source_transcript(window),
            translation=english_translation(window),
            visual_description=window.scene_description,
            rationale=item.rationale,
        )
        for item, window, frame in result.all()
    ]
    return QuestionResponse.model_validate(question).model_copy(update={"evidence": evidence})


async def build_question_responses(session: AsyncSession, questions: list[Question]) -> list[QuestionResponse]:
    return [await build_question_response(session, question) for question in questions]


async def answer_question(session: AsyncSession, video_id: str, question_text: str) -> QuestionResponse:
    started = perf_counter()
    video = await session.get(Video, video_id)
    if not video:
        raise AppError("VIDEO_NOT_FOUND", "Video not found", 404)
    result = await session.scalars(
        select(VideoWindow).where(VideoWindow.video_id == video_id).order_by(VideoWindow.start_time)
    )
    windows = list(result.all())
    if not windows:
        raise AppError("VIDEO_NOT_INDEXED", "Video timeline is not indexed yet")

    answer = _answer_trusted_brand_list_question(question_text, windows)
    if not answer:
        provider = get_ai_provider()
        window_dicts = await retrieve_window_context(session, provider, video_id, question_text)
        storage = get_storage_service()
        with tempfile.TemporaryDirectory() as tmpdir:
            _attach_local_clip_paths(storage, window_dicts, tmpdir)
            try:
                answer = await provider.verify_and_answer_question(video_id, question_text, window_dicts)
            except Exception as exc:
                await log_model_usage(
                    session,
                    provider,
                    request_type="question_answer",
                    video_id=video_id,
                    latency_ms=int((perf_counter() - started) * 1000),
                    estimated_cost=estimated_model_cost("question_answer"),
                    success=False,
                    error_message=str(exc),
                    input_units=len(window_dicts),
                    output_units=0,
                )
                raise
        latency_ms = answer.latency_ms or int((perf_counter() - started) * 1000)
        await log_model_usage(
            session,
            provider,
            request_type="question_answer",
            video_id=video_id,
            latency_ms=latency_ms,
            estimated_cost=answer.estimated_cost or estimated_model_cost("question_answer"),
            input_units=len(window_dicts),
            output_units=len(answer.answer),
        )
    else:
        latency_ms = answer.latency_ms or int((perf_counter() - started) * 1000)

    storage = get_storage_service()

    question = Question(
        video_id=video_id,
        question=question_text,
        answer=answer.answer,
        latency_ms=latency_ms,
        estimated_cost=answer.estimated_cost or estimated_model_cost("question_answer"),
    )
    session.add(question)
    await session.flush()

    response_evidence: list[QuestionEvidenceResponse] = []
    window_by_id = {window.id: window for window in windows}
    with tempfile.TemporaryDirectory() as frame_tmpdir:
        validated_evidence = []
        deferred_items = []  # items that need full video download to extract a frame

        # Fast path: reuse the thumbnail already stored during indexing
        for raw_item in answer.evidence:
            if not isinstance(raw_item, dict):
                continue
            window = window_by_id.get(str(raw_item.get("video_window_id") or ""))
            if not window:
                continue
            existing_frame = await _find_frame(session, window.id)
            if existing_frame:
                timestamp = _safe_timestamp(raw_item.get("timestamp"), window.start_time)
                timestamp = max(window.start_time, min(timestamp, window.end_time))
                validated_evidence.append({
                    "window": window,
                    "frame": existing_frame,
                    "timestamp": timestamp,
                    "rationale": str(raw_item.get("rationale") or "Selected as supporting evidence."),
                })
            else:
                deferred_items.append(raw_item)

        # Slow path: download full video only when no indexed frame exists
        if deferred_items:
            local_video = Path(frame_tmpdir) / video.original_filename
            storage.download_to_path(video.storage_key, local_video)
            for raw_item in deferred_items:
                item = await _validate_and_materialize_evidence_frame(
                    session,
                    storage,
                    video,
                    question.id,
                    window_by_id,
                    raw_item,
                    local_video,
                    frame_tmpdir,
                )
                if item:
                    validated_evidence.append(item)

    if not validated_evidence:
        raise AppError("EVIDENCE_REQUIRED", "Question answer did not include valid timestamp and frame evidence")

    for item in validated_evidence:
        session.add(
            QuestionEvidence(
                question_id=question.id,
                video_window_id=item["window"].id,
                evidence_frame_id=item["frame"].id,
                timestamp=item["timestamp"],
                rationale=item["rationale"],
            )
        )
        response_evidence.append(
            QuestionEvidenceResponse(
                timestamp=item["timestamp"],
                start_time=item["window"].start_time,
                end_time=item["window"].end_time,
                thumbnail_url=storage.get_file_url(item["frame"].storage_key),
                clip_url=storage.get_file_url(item["window"].clip_storage_key) if item["window"].clip_storage_key else None,
                transcript=source_transcript(item["window"]),
                translation=english_translation(item["window"]),
                visual_description=item["window"].scene_description,
                rationale=item["rationale"],
            )
        )
    await session.commit()
    await session.refresh(question)
    return QuestionResponse.model_validate(question).model_copy(update={"evidence": response_evidence})


async def _find_frame(session: AsyncSession, window_id: str) -> EvidenceFrame | None:
    return await session.scalar(select(EvidenceFrame).where(EvidenceFrame.video_window_id == window_id).limit(1))


async def _validate_and_materialize_evidence_frame(
    session: AsyncSession,
    storage,
    video: Video,
    question_id: str,
    window_by_id: dict[str, VideoWindow],
    raw_item: dict,
    local_video: Path,
    tmpdir: str,
) -> dict | None:
    if not isinstance(raw_item, dict):
        return None
    window = window_by_id.get(str(raw_item.get("video_window_id") or ""))
    if not window:
        return None
    try:
        timestamp = float(raw_item.get("timestamp", window.start_time))
    except (TypeError, ValueError):
        timestamp = window.start_time
    if timestamp < window.start_time or timestamp > window.end_time:
        return None
    rationale = str(raw_item.get("rationale") or "Selected as supporting evidence.")
    frame = await _create_evidence_frame_at_timestamp(
        session,
        storage,
        video,
        question_id,
        window,
        timestamp,
        rationale,
        local_video,
        tmpdir,
    )
    if not frame:
        frame = await _find_frame(session, window.id)
    if not frame:
        return None
    return {"window": window, "frame": frame, "timestamp": timestamp, "rationale": rationale}


async def _create_evidence_frame_at_timestamp(
    session: AsyncSession,
    storage,
    video: Video,
    question_id: str,
    window: VideoWindow,
    timestamp: float,
    rationale: str,
    local_video: Path,
    tmpdir: str,
) -> EvidenceFrame | None:
    frame_path = Path(tmpdir) / f"evidence-{window.id}-{int(timestamp * 1000)}.jpg"
    try:
        extract_thumbnail(local_video, frame_path, timestamp)
    except Exception:
        return None
    storage_key = f"evidence/{video.id}/{question_id}/{window.id}-{int(timestamp * 1000)}.jpg"
    storage.upload_path(storage_key, frame_path, "image/jpeg")
    frame = EvidenceFrame(
        video_id=video.id,
        video_window_id=window.id,
        timestamp=timestamp,
        storage_key=storage_key,
        description=rationale,
    )
    session.add(frame)
    await session.flush()
    return frame


def _attach_local_clip_paths(storage, window_dicts: list[dict], tmpdir: str) -> None:
    settings = get_settings()
    attached = 0
    for window in window_dicts:
        if attached >= settings.retrieval_verify_video_top_k:
            break
        clip_key = window.get("clip_storage_key")
        if not clip_key:
            continue
        path = Path(tmpdir) / f"{window['id']}.mp4"
        storage.download_to_path(str(clip_key), path)
        window["local_clip_path"] = str(path)
        attached += 1


def _answer_trusted_brand_list_question(question_text: str, windows: list[VideoWindow]) -> QuestionAnswer | None:
    if not _is_brand_list_question(question_text):
        return None
    brands: dict[str, dict] = {}
    for window in windows:
        for entity in window.detected_entities or []:
            candidate = _trusted_brand_candidate(entity, window)
            if not candidate:
                continue
            brands.setdefault(candidate["key"], candidate)
    if not brands:
        return QuestionAnswer(
            answer="Chưa đủ evidence đọc rõ nhãn hàng trong phiên live.",
            latency_ms=0,
            estimated_cost=0.0,
            evidence=[],
        )
    selected = list(brands.values())
    brand_names = ", ".join(item["brand"] for item in selected)
    evidence = [
        {
            "video_window_id": item["window"].id,
            "timestamp": item["timestamp"],
            "rationale": item["rationale"],
        }
        for item in selected[:5]
    ]
    return QuestionAnswer(
        answer=f"Nhãn hàng đọc/xác nhận được từ evidence đáng tin cậy trong phiên live: {brand_names}.",
        latency_ms=0,
        estimated_cost=0.0,
        evidence=evidence,
    )


def _is_brand_list_question(question_text: str) -> bool:
    normalized = question_text.strip().lower()
    brand_markers = {"nhãn hàng", "nhan hang", "thương hiệu", "thuong hieu", "brand", "hãng", "hang"}
    list_markers = {"nào", "nao", "gì", "gi", "liệt kê", "liet ke", "được nhắc", "duoc nhac", "có", "co"}
    return any(marker in normalized for marker in brand_markers) and any(
        marker in normalized for marker in list_markers
    )


def _trusted_brand_candidate(entity: dict, window: VideoWindow) -> dict | None:
    if not isinstance(entity, dict):
        return None
    entity_type = str(entity.get("type") or "").lower()
    if entity_type not in {"brand", "product"}:
        return None
    if entity.get("is_from_comment") is True:
        return None
    source = str(entity.get("evidence_source") or entity.get("source") or "").lower()
    if source in {
        "comment",
        "live_comment",
        "chat",
        "bottom_product_card",
        "platform_product_card",
        "product_shelf",
        "shopping_shelf",
        "product_card",
        "product_card_ocr",
        "ui_product_card",
    }:
        return None
    brand = str(entity.get("brand") if entity_type == "product" else entity.get("name") or "").strip()
    if not brand or brand.lower() in {"unknown", "none", "null", "n/a"}:
        return None
    haystack = " ".join(
        str(entity.get(key) or "")
        for key in ("name", "brand", "product_name", "evidence_text", "description")
    ).lower()
    if "hannah" in haystack or "whoo x hannah" in haystack or "hannah olala x whoo" in haystack:
        return None
    timestamp = _safe_timestamp(entity.get("timestamp"), window.start_time)
    timestamp = min(window.end_time, max(window.start_time, timestamp))
    return {
        "key": _brand_key(brand),
        "brand": _brand_display_name(brand),
        "window": window,
        "timestamp": timestamp,
        "rationale": f"{_brand_display_name(brand)} được giữ vì xuất hiện ở nguồn evidence đáng tin cậy: {source or 'metadata'}",
    }


def _safe_timestamp(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _brand_key(brand: str) -> str:
    return " ".join(brand.lower().replace("l’", "l'").split())


def _brand_display_name(brand: str) -> str:
    normalized = _brand_key(brand)
    aliases = {
        "loreal": "L'Oreal",
        "l'oreal": "L'Oreal",
        "la roche posay": "La Roche-Posay",
        "la roche-posay": "La Roche-Posay",
    }
    return aliases.get(normalized, brand.strip())
