import tempfile
from pathlib import Path
from time import perf_counter

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.core.exceptions import AppError
from app.models import Claim, ClaimVerification, EvidenceFrame, VideoWindow
from app.schemas.claim import ClaimResponse, ClaimVerificationResponse
from app.services.ai import get_ai_provider
from app.services.storage import get_storage_service
from app.services.usage import estimated_model_cost, log_model_usage

router = APIRouter(prefix="/videos/{video_id}/claims", tags=["claims"])


@router.get("/{claim_id}", response_model=ClaimResponse)
async def claim_detail(video_id: str, claim_id: str, session: AsyncSession = Depends(get_session)) -> Claim:
    claim = await _get_claim(session, video_id, claim_id)
    return claim


@router.post("/{claim_id}/verify", response_model=ClaimVerificationResponse)
async def verify_claim(
    video_id: str,
    claim_id: str,
    session: AsyncSession = Depends(get_session),
) -> ClaimVerificationResponse:
    claim = await _get_claim(session, video_id, claim_id)
    frames = list(
        (
            await session.scalars(select(EvidenceFrame).where(EvidenceFrame.video_window_id == claim.video_window_id))
        ).all()
    )
    window = await session.get(VideoWindow, claim.video_window_id)
    provider = get_ai_provider()
    storage = get_storage_service()
    evidence = [
        {
            "id": frame.id,
            "timestamp": frame.timestamp,
            "description": frame.description,
            "storage_key": frame.storage_key,
            "thumbnail_url": storage.get_file_url(frame.storage_key),
        }
        for frame in frames
    ]
    if window:
        evidence.append(
            {
                "video_window_id": window.id,
                "timestamp": claim.timestamp,
                "start_time": window.start_time,
                "end_time": window.end_time,
                "transcript": window.transcript,
                "scene_description": window.scene_description,
                "ocr_text": window.ocr_text,
                "detected_entities": window.detected_entities,
                "chunk_metadata": window.chunk_metadata,
            }
        )
    started = perf_counter()
    with tempfile.TemporaryDirectory() as tmpdir:
        if window and window.clip_storage_key:
            clip_path = Path(tmpdir) / f"{window.id}.mp4"
            storage.download_to_path(window.clip_storage_key, clip_path)
            evidence[-1]["local_clip_path"] = str(clip_path)
        try:
            result = await provider.verify_claim(claim.claim_text, evidence)
            await log_model_usage(
                session,
                provider,
                request_type="claim_verify",
                video_id=video_id,
                latency_ms=int((perf_counter() - started) * 1000),
                estimated_cost=estimated_model_cost("claim_verify"),
                input_units=len(evidence),
                output_units=len(result.explanation),
            )
        except Exception as exc:
            await log_model_usage(
                session,
                provider,
                request_type="claim_verify",
                video_id=video_id,
                latency_ms=int((perf_counter() - started) * 1000),
                estimated_cost=estimated_model_cost("claim_verify"),
                success=False,
                error_message=str(exc),
                input_units=len(evidence),
            )
            await session.commit()
            raise
    verification = ClaimVerification(
        claim_id=claim.id,
        verdict=result.verdict,
        explanation=result.explanation,
        confidence=result.confidence,
        evidence_frame_ids=result.evidence_frame_ids,
    )
    session.add(verification)
    await session.commit()
    return ClaimVerificationResponse(
        claim_id=claim.id,
        claim_text=claim.claim_text,
        timestamp=claim.timestamp,
        verdict=result.verdict,
        confidence=result.confidence,
        explanation=result.explanation,
        evidence=[{key: value for key, value in item.items() if key != "local_clip_path"} for item in evidence],
    )


async def _get_claim(session: AsyncSession, video_id: str, claim_id: str) -> Claim:
    claim = await session.scalar(select(Claim).where(Claim.video_id == video_id, Claim.id == claim_id))
    if not claim:
        raise AppError("CLAIM_NOT_FOUND", "Claim not found", status.HTTP_404_NOT_FOUND)
    return claim
