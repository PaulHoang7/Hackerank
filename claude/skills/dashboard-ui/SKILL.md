---
name: dashboard-ui
description: Use when building the frontend — upload + processing status, the indexed timeline viewer, multilingual transcript explorer with search, the SKU/product timeline, the Q&A interface that renders grounded results (jump-to-timestamp, thumbnail, rationale, verified badge), the compliance view, and the LIVE cost/latency/throughput dashboard required during the demo. Stage 7. Read 00-overview first.
---

# dashboard-ui · Stage 7 (Frontend & Observability)

The surface judges interact with. Every result must show its grounding (timestamp + thumbnail + rationale), and cost/latency must be live.

## When to use
Building or wiring any user-facing view, or the observability dashboard.

## Views
1. **Upload & status** — drop video/URL + optional context kit; show job `status` (queued → ingested → indexed) and progress.
2. **Indexed timeline** — scenes, dialogue, audio events, on-screen text, entities, and the **energy curve**; click to seek.
3. **Transcript explorer** — multilingual (`transcript_original` + `text_en`), text search, jump-by-timestamp; highlight code-switching.
4. **SKU / product timeline** — per entity: shown/mentioned/demoed/priced/compared, ranked by visibility, with thumbnails (from entity-sku-timeline).
5. **Q&A** — chat box; render each answer with **jump-to-timestamp + thumbnail + rationale (≥2 modalities) + verified badge**; show "not found" honestly when refused.
6. **Compliance view** — flagged violations with paired audio + frame evidence and severity.
7. **Live cost/latency/throughput dashboard (mandatory)** — read `_meta` aggregates: tokens, cost (USD), latency, throughput (videos/min, windows/s), cache-hit rate. Update live during indexing + queries.

## Data sources
- Grounded answers → `grounded-qa`; verifications/compliance → `claim-visual-verification`; timelines → `entity-sku-timeline`; search → `retrieval-index`; metrics → `_meta` captured by `seed-omni-reasoning`.

## Gotchas / locked decisions
- The dashboard is a **judging criterion** — make cost/latency prominent and real-time, not a static number.
- Every answer card must visibly carry its grounding; no bare text answers.
- Thumbnails are URLs to storage (binary never inlined in records).

## Definition of done
Judge can upload, watch indexing progress + live cost/latency, explore timeline/transcript/SKU views, ask grounded questions (with seek + thumbnail + rationale), and see compliance flags — all within the demo window.
