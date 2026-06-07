# BX-T4 Video Intelligence Backend

FastAPI backend for indexing ecommerce videos with Seed 2.0 and answering questions with timestamped evidence.

## Runtime Shape

- FastAPI API server for upload, querying, metrics and job status.
- Dramatiq worker for video indexing.
- PostgreSQL for metadata.
- Redis for Dramatiq.
- Local filesystem storage for uploaded videos and thumbnails.
- Seed 2.0 via BytePlus Ark Chat API for video window understanding, QA and claim verification.
- Gemini Embedding for question/chunk semantic retrieval.

## Processing Flow

```text
POST /api/v1/videos/upload
-> validate video
-> store original video
-> create Video and ProcessingJob
-> enqueue worker
-> ffprobe duration
-> split into fixed 30s chunks with 5s overlap
-> extract thumbnail + short mp4 clip per chunk
-> send chunk clip to Seed 2.0
-> validate strict JSON response
-> build focused index_text from visual/OCR/product metadata
-> embed index_text and persist pgvector embedding
-> persist VideoWindow, EvidenceFrame and Claim
-> consolidate product candidates into verified products and ProductOccurrence timeline
-> user question embedding
-> pgvector retrieve + lexical fallback
-> Seed rerank top candidates
-> Seed verifies top chunk clips + metadata
-> extract evidence frame at the answer timestamp
-> answer with video chunk, timestamp and thumbnail/clip evidence
-> log model calls, latency, success/failure and configurable cost estimates
```

Seed video understanding is used for visual description, OCR, product/entity/action extraction, business events and visual claim evidence. Per Seed video documentation, audio understanding from video files is not supported, so production-grade speech transcript requires a separate ASR layer.

## Local Run

```bash
cp .env.example .env
docker compose up --build
```

Swagger:

```text
http://localhost:8000/docs
```

Local files are stored under `./storage` and ignored by git.

## Environment

Required for real Seed video analysis and Gemini retrieval:

```env
AI_PROVIDER=seed
SEED_OMNI_API_KEY=your_key
SEED_OMNI_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3
SEED_OMNI_MODEL=seed-2-0-mini-260428
SEED_OMNI_FALLBACK_MODELS=seed-2-0-lite-260228
SEED_OMNI_VIDEO_FPS=5
SEED_OMNI_MAX_TOKENS=2400
SEED_OMNI_MAX_VIDEO_BYTES=52428800
SEED_OMNI_THINKING_ENABLED=true
SEED_OMNI_REASONING_EFFORT=low
SEED_OMNI_ESTIMATED_COST_PER_REQUEST=0
GEMINI_API_KEYS=your_gemini_key_1,your_gemini_key_2
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSIONS=1024
GEMINI_EMBEDDING_ESTIMATED_COST_PER_REQUEST=0
VIDEO_CHUNK_SECONDS=30
VIDEO_CHUNK_OVERLAP_SECONDS=5
RETRIEVAL_VECTOR_TOP_K=24
RETRIEVAL_RERANK_TOP_K=8
RETRIEVAL_VERIFY_VIDEO_TOP_K=3
EXTERNAL_API_TIMEOUT_SECONDS=120
```

Gemini embeddings are required for retrieval. The app uses `RETRIEVAL_DOCUMENT` for indexed chunks and `RETRIEVAL_QUERY` for user questions. `GEMINI_API_KEYS` accepts one key or multiple comma-separated keys for rotation. If it is empty, indexing and question retrieval will fail with `GEMINI_EMBEDDING_NOT_CONFIGURED`.

`SEED_OMNI_MODEL` is the required primary model for the challenge. `SEED_OMNI_FALLBACK_MODELS` keeps the demo running if the Ark account has not activated the primary model yet; remove the fallback when the primary model is available.

Other important variables:

```env
DATABASE_URL=postgresql+asyncpg://bxt4:bxt4@postgres:5432/bxt4
SYNC_DATABASE_URL=postgresql+psycopg://bxt4:bxt4@postgres:5432/bxt4
REDIS_URL=redis://redis:6379/0
STORAGE_PROVIDER=local
LOCAL_STORAGE_PATH=./storage
STORAGE_PUBLIC_URL=/storage
MAX_UPLOAD_SIZE_BYTES=1073741824
```

Never commit real API keys.

## Endpoints

- `GET /api/v1/health`
- `GET /api/v1/health/ready`
- `POST /api/v1/videos/upload`
- `POST /api/v1/videos/import-url`
- `GET /api/v1/videos`
- `GET /api/v1/videos/{video_id}`
- `DELETE /api/v1/videos/{video_id}`
- `GET /api/v1/videos/{video_id}/timeline`
- `GET /api/v1/videos/{video_id}/transcript`
- `GET /api/v1/videos/{video_id}/products`
- `GET /api/v1/videos/{video_id}/claims`
- `GET /api/v1/videos/{video_id}/metrics`
- `GET /api/v1/jobs/{job_id}`
- `POST /api/v1/videos/{video_id}/questions`
- `GET /api/v1/videos/{video_id}/questions`
- `GET /api/v1/videos/{video_id}/questions/{question_id}`
- `GET /api/v1/videos/{video_id}/claims/{claim_id}`
- `POST /api/v1/videos/{video_id}/claims/{claim_id}/verify`
- `GET /api/v1/metrics/overview`

`POST /api/v1/videos/import-url` accepts configured public TikTok/Douyin URLs, imports the media with `yt-dlp`, stores it as a normal video, then queues the indexing pipeline. It does not bypass private, login-only, DRM, or protected content.

## Manual API Test

Start the stack:

```bash
docker compose up --build
```

Open Swagger and test the endpoints directly:

```text
http://localhost:8000/docs
```

Suggested flow:

1. `GET /api/v1/health/ready`
2. `POST /api/v1/videos/upload`
3. `GET /api/v1/jobs/{job_id}`
4. `GET /api/v1/videos/{video_id}/timeline`
5. `POST /api/v1/videos/{video_id}/questions`

## Current Limits

- Seed multimodal transcript/audio quality depends on the activated `SEED_OMNI_MODEL` and the source video's audio clarity.
- Real semantic retrieval requires `GEMINI_API_KEYS`.
- Product/SKU precision depends on readable package labels, product-card OCR or clear spoken evidence.
- `SEED_OMNI_ESTIMATED_COST_PER_REQUEST` and `GEMINI_EMBEDDING_ESTIMATED_COST_PER_REQUEST` must be set to real pricing for non-zero demo cost estimates.
- Window-level partial retry is still basic.
- Local storage is intended for demo/dev; add TOS/S3 for production deployment.
