from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import ModelUsageLog
from app.services.ai.base import VideoIntelligenceProvider


async def log_model_usage(
    session: AsyncSession,
    provider: VideoIntelligenceProvider,
    request_type: str,
    latency_ms: int,
    video_id: str | None = None,
    estimated_cost: float = 0.0,
    success: bool = True,
    error_message: str | None = None,
    input_units: int = 0,
    output_units: int = 0,
) -> None:
    session.add(
        ModelUsageLog(
            video_id=video_id,
            request_type=request_type,
            provider=provider.name,
            model_name=provider.model_name,
            latency_ms=latency_ms,
            input_units=input_units,
            output_units=output_units,
            estimated_cost=estimated_cost,
            success=success,
            error_message=error_message,
        )
    )


def estimated_model_cost(request_type: str) -> float:
    settings = get_settings()
    if request_type.startswith("embedding"):
        return float(settings.gemini_embedding_estimated_cost_per_request)
    return float(settings.seed_omni_estimated_cost_per_request)
