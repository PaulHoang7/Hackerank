---
name: grounded-qa
description: Use when implementing the natural-language Q&A endpoint over an indexed video — retrieve relevant windows, synthesize an answer with the model, and ENFORCE the grounding contract (every answer carries ≥1 timestamp + ≥1 thumbnail + a rationale citing ≥2 modalities; ungrounded answers are refused). Stage 6a. Read 00-overview first.
---

# grounded-qa · Stage 6a (Grounded Q&A)

Answer free-form questions about an indexed video. **No evidence → no affirmative answer.** This skill owns the grounding contract.

## When to use
A user asks a natural-language question (e.g., "when did the host demo product 27?").

## Inputs → Outputs
- **In:** `video_id`, question (any supported language).
- **Out:** answer + `evidence[]` (timestamp + thumbnail + transcript/ocr/visual) + `rationale` + `_meta` (latency, cost).

## Steps
1. **Resolve & retrieve** — via `retrieval-index`: resolve entity refs → hybrid retrieve top-k windows → neighbor expansion. (For "find every…" use the exhaustive mode.)
2. **Synthesize** — pass ONLY the retrieved windows to the model (`reasoning_effort: medium/high`) to compose the answer.
3. **Enforce grounding** — the response MUST include:
   - **≥1 timestamp** (use `word_timestamps`/`ocr[].t` for **±3s**),
   - **≥1 frame thumbnail**,
   - **rationale citing ≥2 of {audio, visual, dialogue}** (e.g., "audio said '299k', overlay showed '299K'").
4. **Refuse when unsupported** — if retrieval yields no qualifying evidence, return a non-affirmative ("not found in this video") rather than a guess.

## Response shape
```json
{
  "answer": "The host priced the product at 00:02:00–00:02:05.",
  "rationale": "Dialogue: 'giảm còn 299k'; Visual/OCR: overlay '299K' + 'FREE SHIP'.",
  "evidence": [{ "start_time": 120, "end_time": 125, "thumbnail_path": "...",
    "transcript": "...", "ocr": ["299K","FREE SHIP"], "visual_description": "..." }],
  "latency_ms": 1320, "cost": 0.002
}
```

## Gotchas / locked decisions
- Grounding is enforced **in code**, not left to the model — drop any answer lacking timestamp+thumbnail.
- Timestamps come from intra-window data, so window size doesn't cap accuracy.
- Cross-language: retrieve on `text_en`, but cite evidence in the original language.

## Definition of done
Answers carry real ±3s timestamps + thumbnails + a ≥2-modality rationale; unsupported questions are refused; `_meta` recorded for the dashboard.
