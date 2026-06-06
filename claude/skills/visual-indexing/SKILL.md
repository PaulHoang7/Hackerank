---
name: visual-indexing
description: Use when extracting visual metadata per window — scene description, on-screen text (OCR), visible products, people, actions, and business events. Uses the hybrid approach (native video by segment at low-res for coverage + targeted high-res crops for OCR). Stage 3 of the pipeline. Calls the model via seed-omni-reasoning. Read 00-overview first.
---

# visual-indexing · Stage 3 (Visual Pass — Hybrid)

Understand the *picture*, aligned to the already-available transcript. **Hybrid feed (locked):** native video by segment (cheap, full temporal coverage + motion) + targeted high-res for on-screen text (OCR/compliance accuracy).

## When to use
After audio pass, to fill the visual fields of the index.

## Inputs → Outputs
- **In:** video (segments or Files-API file), window list, each window's `transcript_en` (as context).
- **Out:** per-window `visual_description, ocr[], products_raw[], people[], actions[], business_events[]`.

## Steps
1. **Primary pass — native video by segment** (~10 min/segment, aligned with audio blocks): send natively at **fps 1, low-res (64 tok/frame)** — a 10-min segment ≈ 600 frames ≈ 38k tokens (< 80k budget). Force structured output (function calling) returning a **record per window** (use PySceneDetect boundaries; pass `transcript_en` so business events fuse audio+visual).
   - Produces: `visual_description`, `products_raw`, `people`, `actions` (holding/demo/pointing — motion is why native video beats static frames), coarse `ocr`, `business_events`.
2. **OCR/compliance pass — targeted high-res** for windows flagged with on-screen text or business events:
   - Prefer **cropping the text region** (price tag, FREE SHIP, % off, certificate) and sending that crop **full-res** → sharp + cheap (small image), avoids the 670k-px/frame downscale that blurs small text in a full 1080p frame.
   - Refine `ocr[]` with text + timestamp.
3. **Merge** primary + OCR results into each window record; dedupe OCR/business_event entries within ~1s.

## Seed usage
`reasoning_effort: low`; primary pass image quality `low`; OCR crops `xhigh`. Enable prefix cache for the identical extraction system prompt across segments.

## Writes to Index
`visual_description, ocr[], products_raw[], people[], actions[], business_events[]` per window. (`products_raw` are free-text descriptions — `entity-sku-timeline` canonicalizes them next.)

## Gotchas / locked decisions
- **Watch OCR resolution:** native low-res blurs small text → always do the high-res crop pass for text-bearing windows (compliance depends on it).
- High-res cannot cover a long segment in one call (≤80k budget → ~213 high-res frames) — that's why OCR is *targeted*, not global.
- `business_events` must reconcile spoken ("299k") and on-screen ("299K") — pass transcript into the visual call.

## Definition of done
Every window has visual fields; text-bearing windows have sharp OCR with timestamps; actions captured for demo/holding moments.
