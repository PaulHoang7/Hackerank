from fastapi import APIRouter

from app.api.v1 import claims, health, jobs, metrics, questions, videos

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(videos.router)
api_router.include_router(jobs.router)
api_router.include_router(questions.router)
api_router.include_router(claims.router)
api_router.include_router(metrics.router)
