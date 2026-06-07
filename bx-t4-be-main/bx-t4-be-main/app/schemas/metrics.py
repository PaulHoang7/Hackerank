from pydantic import BaseModel


class MetricsOverviewResponse(BaseModel):
    videos_total: int
    videos_indexed: int
    jobs_processing: int
    questions_total: int
    estimated_cost_total: float
    average_latency_ms: float
    model_calls_total: int
    model_calls_failed: int
    average_model_latency_ms: float
