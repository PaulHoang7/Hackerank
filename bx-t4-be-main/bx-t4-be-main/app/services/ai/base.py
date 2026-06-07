from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.models.enums import Verdict


@dataclass(frozen=True)
class VideoWindowInput:
    video_id: str
    start_time: float
    end_time: float
    local_video_path: Path
    thumbnail_path: Path | None = None
    clip_path: Path | None = None


@dataclass(frozen=True)
class VideoWindowAnalysis:
    transcript: str
    translation: str | None
    language: str | None
    speech_segments: list[dict]
    scene_description: str
    ocr_text: list[dict]
    visual_evidence: list[dict]
    audio_events: list[dict]
    detected_entities: list[dict]
    energy_score: float
    emotion: str | None
    claims: list[dict]


@dataclass(frozen=True)
class QuestionAnswer:
    answer: str
    latency_ms: int
    estimated_cost: float
    evidence: list[dict]


@dataclass(frozen=True)
class ClaimVerificationResult:
    verdict: Verdict
    explanation: str
    confidence: float
    evidence_frame_ids: list[str]


class VideoIntelligenceProvider(ABC):
    name: str
    model_name: str

    @abstractmethod
    async def analyze_video_window(self, window: VideoWindowInput) -> VideoWindowAnalysis:
        raise NotImplementedError

    @abstractmethod
    async def answer_question(self, video_id: str, question: str, windows: list[dict]) -> QuestionAnswer:
        raise NotImplementedError

    @abstractmethod
    async def verify_claim(self, claim_text: str, evidence: list[dict]) -> ClaimVerificationResult:
        raise NotImplementedError

    @abstractmethod
    async def detect_products(self, video_id: str, windows: list[dict]) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def generate_embedding(self, text: str, *, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        raise NotImplementedError

    async def rerank_windows(self, question: str, windows: list[dict], limit: int) -> list[dict]:
        return windows[:limit]

    async def verify_and_answer_question(self, video_id: str, question: str, windows: list[dict]) -> QuestionAnswer:
        return await self.answer_question(video_id, question, windows)
