from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.schemas.metrics import MetricsOverviewResponse
from app.services.metrics.service import overview

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/overview", response_model=MetricsOverviewResponse)
async def metrics_overview(session: AsyncSession = Depends(get_session)) -> MetricsOverviewResponse:
    return await overview(session)
