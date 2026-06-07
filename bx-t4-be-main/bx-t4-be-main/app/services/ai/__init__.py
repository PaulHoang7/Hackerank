from app.core.config import get_settings
from app.core.exceptions import AppError
from app.services.ai.base import VideoIntelligenceProvider
from app.services.ai.seed_omni_provider import SeedOmniVideoIntelligenceProvider


def get_ai_provider() -> VideoIntelligenceProvider:
    settings = get_settings()
    if settings.ai_provider == "seed":
        return SeedOmniVideoIntelligenceProvider(settings)
    raise AppError("AI_PROVIDER_UNSUPPORTED", f"Unsupported AI provider: {settings.ai_provider}")
