# SEA E-commerce Video Intelligence — AI Backend

Multimodal / Video-RAG backend for Southeast-Asian e-commerce video (TikTok Shop /
Shopee Live). Ingests a video **once**, turns it into a **grounded, queryable index**,
and answers questions tied to **timestamp + frame thumbnail + cross-modal rationale**.

**This repo is the AI + API layer only.** The web frontend is built separately and
talks to this backend over the REST API below; both share the **SQLite** DB.

- **Model:** Seed 2.0 Lite **only** (`seed-2-0-lite-260428`) via BytePlus ModelArk
  (OpenAI-compatible). Every model call goes through one wrapper (`app/seed_client.py`).
- **Grounding rule (enforced in code):** every affirmative answer carries ≥1 timestamp
  (±3s) + ≥1 thumbnail + a rationale citing ≥2 of {audio/dialogue, visual, ocr}.
  Otherwise it refuses ("not found in this video").

---

## Pipeline → file map

| Stage | What | File |
|------:|------|------|
| 0–1 | intake, proxy, scene-aware windows, thumbnails, audio extraction | `app/ingestion.py` |
| — | the Seed 2.0 Lite client (input methods, forced structured output, cost/latency) | `app/seed_client.py` |
| 2 | ASR + speech-translation + diarization + audio events + energy curve | `app/audio.py` |
| 3 | native-video segment pass + targeted high-res OCR → scene/ocr/products/actions/events | `app/visual.py` |
| 4 / 6d | canonical entities, Re-ID, occurrence inverted index, SKU timeline | `app/entities.py` |
| 5 | retrieval_text, multilingual embeddings, Chroma + hybrid/exhaustive search | `app/retrieval.py` |
| 6a | grounded NL Q&A (grounding enforced) | `app/qa.py` |
| 6b/6c | claim-vs-visual, compliance, temporal | `app/verification.py` |
| — | orchestrator (status, caching, cost aggregation) | `app/pipeline.py` |
| — | SQLite source-of-truth + metrics | `app/db.py` |
| — | FastAPI surface for the web team | `app/main.py` |
| — | canonical Pydantic data contract | `app/schema.py` |

---

## Setup

```bash
# from project root
cp .env.example .env          # set ARK_API_KEY=...
uv venv backend/.venv --python 3.13
uv pip install --python backend/.venv/bin/python -r backend/requirements.txt
# requires ffmpeg + ffprobe on PATH
```

## Index a video

```bash
# CLI
backend/.venv/bin/python backend/index_video.py "ScreenRecording_06-06-2026 10-40-29_1.mp4"
# or via the API (see /api/ingest)
```

Indexing the 5.5-min sample = **~130s, ~$0.07** total (audio + visual + entities).
Stage outputs are cached to `storage/index/<id>.<stage>.json`, so re-runs are free.

## Run the API

```bash
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

---

## REST API (what the web frontend calls)

Base: `http://<host>:8000`. CORS is open. Thumbnails are served at `/thumbs/...`.

### Ingest & status
- `POST /api/ingest` — multipart: `file` (upload) **or** `source` (filename under `data/`),
  optional `video_id`. Starts background indexing → `{video_id, status:"queued"}`.
- `GET  /api/videos` — list indexed videos.
- `GET  /api/videos/{id}/status` — job `{status, progress 0..1, stage, message}`
  (poll while `status != "indexed"`).
- `GET  /api/videos/{id}` — video meta + `totals` (cost/tokens) + `stage_timings`.

### Index views (timeline / transcript / SKU)
- `GET  /api/videos/{id}/windows` — full per-window records (timeline, OCR, products,
  actions, business_events, entities, energy, `_meta`). The canonical index.
- `GET  /api/videos/{id}/transcript` — multilingual transcript per window
  (`transcript_original`, `transcript_en`, `lang_spans`, `speaker`, `audio_events`, `energy`).
- `GET  /api/videos/{id}/energy` — `[{t, energy}]` for the energy curve.
- `GET  /api/videos/{id}/entities` — canonical products `{entity_id, type, names{vi,en,th,brand}}`.
- `GET  /api/videos/{id}/timeline/{entity_id}` — SKU timeline: occurrences ordered &
  **visibility-ranked**, with thumbnails (shown/mentioned/demoed/priced/compared).

### Q&A & verification (return grounded evidence)
- `POST /api/videos/{id}/qa` — `{question}` → `{answer, found, rationale, modalities,
  evidence[], cost, latency_ms}`. `evidence[]` = `{start_time, end_time, thumbnail_path,
  transcript, transcript_en, ocr[], visual_description}`. `found:false` ⇒ render the refusal.
- `POST /api/videos/{id}/verify` — `{claim, window_id?}` → claim-vs-visual
  `{result: verified|not_supported|warning, is_verified, reason, evidence[]}`.
- `GET  /api/videos/{id}/compliance` — hybrid rule+model audit →
  `{checked, flags:[{rule, result, severity, reason, evidence[]}]}`.
- `POST /api/videos/{id}/temporal` — `{entity_id?, business_event?}` → exhaustive
  intersection `{count, matches[]}` (e.g. sku visible **while** price shown).

### Live metrics (the mandatory dashboard)
- `GET  /api/metrics?video_id={id}` — `{calls, cost_usd, prompt/audio/output tokens,
  avg_latency_ms, cache_hit_rate, by_stage[], throughput{windows, windows_per_sec, ...}}`.
- `GET  /api/videos/{id}/video` — the source file (range-enabled) for the seek player.
- `GET  /api/health`.

---

## Shared SQLite DB

Path: `storage/app.sqlite3` (override `SQLITE_PATH`). **WAL mode** → the web app can read
concurrently while indexing writes. Tables: `videos`, `jobs`, `windows`, `entities`,
`occurrences`, `calls` (every model call → powers `/api/metrics`). The DB is the
auditable source of truth; Chroma (`storage/chroma/`) is only the vector speed layer.

`business_events` vocabulary: `price_mention, discount_mention, free_ship_mention,
authenticity_claim, product_demo, buy_now_cta, stock_count, voucher_mention, comparison`.

## Cost levers (already built in)
Audio billed once · `reasoning_effort` low for indexing, medium/high for Q&A/verify ·
high-res image only for OCR crops · scene-aware windows · ≤80k video tokens/request.
