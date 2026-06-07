import json
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Dimension of the local multilingual embedding model (paraphrase-multilingual-MiniLM-L12-v2).
# Used by the ORM Vector column and the alembic migration so they stay in lockstep.
EMBEDDING_DIMENSIONS = 384


class Settings(BaseSettings):
    app_name: str = "BX-T4 Video Intelligence Engine"
    environment: str = "local"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    database_url: str = "postgresql+asyncpg://bxt4:bxt4@localhost:5432/bxt4"
    sync_database_url: str = "postgresql+psycopg://bxt4:bxt4@localhost:5432/bxt4"
    redis_url: str = "redis://localhost:6379/0"

    storage_provider: str = "local"
    local_storage_path: str = "./storage"
    storage_public_url: str = "/storage"

    ai_provider: str = "seed"
    seed_omni_api_key: str | None = None
    seed_omni_base_url: str = "https://ark.ap-southeast.bytepluses.com/api/v3"
    seed_omni_model: str = "seed-2-0-mini-260428"
    seed_omni_fallback_models: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["seed-2-0-lite-260228"])
    seed_omni_video_fps: float = 1.0
    seed_omni_max_tokens: int = 1200
    seed_omni_max_video_bytes: int = 50 * 1024 * 1024
    seed_omni_thinking_enabled: bool = True
    seed_omni_reasoning_effort: str = "low"
    seed_omni_estimated_cost_per_request: float = 0.0083

    # Embeddings: local SentenceTransformer (offline, free, multilingual) — unified
    # with the backend/ Streamlit AI layer. Set embedding_provider=gemini to revert.
    embedding_provider: str = "local"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimensions: int = EMBEDDING_DIMENSIONS

    gemini_api_keys: Annotated[list[str], NoDecode] = Field(default_factory=list)
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dimensions: int = 1024
    gemini_embedding_estimated_cost_per_request: float = 0.0001

    external_api_timeout_seconds: int = 30

    video_chunk_seconds: float = 30.0
    video_chunk_overlap_seconds: float = 5.0
    video_max_chunks: int = 240
    # How many chunks to analyze concurrently (Seed + embedding fan-out).
    seed_analysis_concurrency: int = 5
    retrieval_vector_top_k: int = 24
    retrieval_rerank_top_k: int = 8
    retrieval_verify_video_top_k: int = 3

    max_upload_size_bytes: int = 1_073_741_824
    allowed_video_content_types: list[str] = Field(
        default_factory=lambda: ["video/mp4", "video/quicktime", "video/webm"]
    )
    external_import_max_size_bytes: int = 1_073_741_824
    external_import_timeout_seconds: int = 600
    external_import_allowed_hosts: list[str] = Field(
        default_factory=lambda: [
            "tiktok.com",
            "www.tiktok.com",
            "vm.tiktok.com",
            "vt.tiktok.com",
            "douyin.com",
            "www.douyin.com",
            "v.douyin.com",
            "live.douyin.com",
        ]
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator(
        "cors_origins",
        "allowed_video_content_types",
        "external_import_allowed_hosts",
        "gemini_api_keys",
        "seed_omni_fallback_models",
        mode="before",
    )
    @classmethod
    def parse_csv(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
