---
name: 00-overview
description: Read FIRST before any work on this SEA e-commerce video-intelligence project. Defines the mission, the mandatory constraints (Seed 2.0 Lite only, TRAE, grounding rule, multilingual, live cost/latency), the canonical Index JSON schema that every other skill reads/writes, the glossary, the cost levers, and the pipeline-to-skill map. Every other skill references this.
---

# 00 · Project Overview & Shared Contract

A **Multimodal / Video RAG** system: ingest e-commerce video (live streams, UGC reviews, ad variants, influencer deliverables) **once**, turn it into a **grounded, queryable index**, then answer questions in any order with answers tied to **timestamp + frame thumbnail + cross-modal rationale**. The value is the *answer*, not rendered clips.

## Mandatory constraints (non-negotiable — these are judged)
- **Model: Seed 2.0 Lite ONLY** for ALL cross-modal work — ASR, translation, OCR, scene description, entity tracking, audio events, Q&A, claim-vs-visual. **API Model ID: `seed-2-0-lite-260428`** (display name "Dola-Seed-2.0-lite/260428"). See `seed-omni-reasoning`.
- **Built & shipped on TRAE.**
- **Grounding rule:** every answer ties to **≥1 timestamp AND ≥1 frame thumbnail**, with a rationale citing **≥2 of {audio, visual, dialogue}**. No supporting evidence → no affirmative answer.
- **Multilingual:** ≥2 SEA languages with code-switching. Recommended demo pair: **vi + th** (or vi + id) — these have both ASR + speech-translation to English. Tagalog (`fil`) has ASR only.
- **Live cost / latency / throughput dashboard** during the demo.
- **Timestamp accuracy target: ±3s.**

## Pipeline → skill map
| Stage | What | Skill |
|---|---|---|
| 0–1 | intake, storage, queue, scene-aware windowing, frame/thumbnail/audio extraction | `video-ingestion` |
| — | the Seed 2.0 Lite client used by every model call | `seed-omni-reasoning` |
| 2 | audio pass: ASR + AST + timestamps + diarization + audio events + energy + `text_en` | `audio-understanding` |
| 3 | visual pass: hybrid native-video + high-res OCR → scene/ocr/products/actions/business_events | `visual-indexing` |
| 4 + 6d | canonical entity registry, Re-ID, multilingual alias, occurrence index, SKU timeline | `entity-sku-timeline` |
| 5 | build retrieval_text, validate, embed, vector store, hybrid search + neighbor expansion | `retrieval-index` |
| 6a | natural-language grounded Q&A | `grounded-qa` |
| 6b/6c | claim-vs-visual verification, compliance, temporal retrieval | `claim-visual-verification` |
| 7 | frontend + live cost/latency dashboard | `dashboard-ui` |

## Canonical Index JSON (THE data contract — all skills conform)

```jsonc
// ── one record per WINDOW ──
{
  "window_id": "w_024", "video_id": "video_001",
  "start_time": 134.0, "end_time": 142.5,                 // scene-aware seconds
  "thumbnails": ["/thumbs/v001_134.jpg", "/thumbs/v001_138.jpg"],
  // from AUDIO pass (audio-understanding)
  "transcript_original": "cái serum này hôm nay sale còn 299k",
  "transcript_en": "this serum is on sale for 299k today",
  "lang_spans": [{ "vi": "cái serum này..." }, { "en": "sale" }],
  "speaker": "host_main",
  "word_timestamps": [{ "w": "sale", "t": 136.2 }],        // enables ±3s
  "audio_events": ["high_energy_voice"], "energy": 0.82,   // 0..1, for energy curve
  // from VISUAL pass (visual-indexing)
  "visual_description": "Host holds a white serum bottle close to camera",
  "ocr": [{ "text": "299K", "t": 137.0 }, { "text": "FREE SHIP", "t": 137.0 }],
  "products_raw": ["white serum bottle"], "people": ["host"],
  "actions": ["holding_product", "product_demo"],
  "business_events": ["price_mention", "discount_mention", "product_demo"],
  // from ENTITY RESOLUTION (entity-sku-timeline)
  "entities": ["sku_27"],                                  // canonical ids, NOT free strings
  // from ASSEMBLE (retrieval-index)
  "retrieval_text": "serum 299K FREE SHIP host holds demo price_mention discount ...",
  "_meta": { "model": "Dola-Seed-2.0-lite/260428", "cost_usd": 0.0009, "latency_ms": 740, "reasoning_effort": "low" }
}

// ── canonical entity registry ──
{ "entity_id": "sku_27", "type": "product",
  "names": { "vi": "kem nền Cocoon", "en": "Cocoon foundation", "brand": "Cocoon" },
  "ref_images": ["tos://catalog/sku27.jpg"], "visual_embedding": [/* ... */] }

// ── occurrence inverted index: entity → every appearance ──
{ "sku_27": [
  { "window_id": "w_024", "start_time": 134.0, "end_time": 142.5,
    "action": "product_demo", "visibility": 0.86, "thumbnail": "/thumbs/v001_134.jpg",
    "evidence": { "visual": 0.91, "ocr": "Cocoon", "dialogue_lang": "vi" } }
]}
```

## Glossary
- **segment** — ~5–10 min audio/video block processed in ONE model pass (cost/context unit; see audio-understanding, visual-indexing).
- **window** — 8–15s **scene-aware** retrieval unit. Windows are **contiguous** (share the boundary frame, no gaps); use ~1s overlap **only** at artificial sub-splits of a long scene, then dedupe.
- **frame** — a sampled image, used for visual understanding and/or as thumbnail evidence.
- **occurrence** — one appearance of a canonical entity inside a window.

## Cost levers (build them in — they show on the dashboard)
1. **Audio billed once** — process each audio second exactly once; never re-send per overlapping window.
2. **`reasoning_effort`** — `low`/`minimal` for indexing; `medium`/`high` only for Q&A / verification.
3. **Prefix / explicit cache** — the extraction system prompt is identical across windows; cache it.
4. **Per-frame image quality** — `xhigh` only for OCR frames; `low` for general scene.
5. **Scene-aware windows** — far fewer calls than fixed 5s windows.
6. **Seed video budget** — ≤80k tokens/video; ~1280 low-res frames (64 tok) OR ~213 high-res frames (384 tok) per call.

## Definition of done (project)
Judge uploads ≥10–15 min of e-commerce video and, within the demo window, gets: indexed timeline (scenes, dialogue, audio events, on-screen text, entities, energy curve), multilingual transcript explorer (≥2 SEA langs) with search, SKU/product timeline, grounded NL Q&A, claim-vs-visual verification, temporal/compliance retrieval, and a live cost/latency/throughput dashboard.
