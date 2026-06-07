import asyncio

import dramatiq

from app.workers.broker import broker
from app.workers.pipeline import run_video_pipeline

_ = broker


@dramatiq.actor(max_retries=2, time_limit=30 * 60 * 1000)
def process_video(video_id: str, job_id: str) -> None:
    asyncio.run(run_video_pipeline(video_id, job_id))
