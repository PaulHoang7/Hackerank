---
name: seed-omni-reasoning
description: Use for ANY call to the Seed 2.0 Lite model (the only allowed model) — building the client, choosing the input method (Files API / base64 / URL), forcing structured output via function calling, setting reasoning_effort, using prefix cache, handling thinking-summary fields, respecting the video token budget, and capturing per-call cost/latency. Every other AI skill calls the model THROUGH this wrapper. Read 00-overview first.
---

# seed-omni-reasoning · The Model Engine

Single chokepoint for every Seed 2.0 Lite call. Centralizes correctness, cost control, and observability so no other skill talks to the model directly.

## Model & API facts (from the API reference)
- **Platform:** BytePlus ModelArk, **OpenAI-compatible**. Base URL (SEA): `https://ark.ap-southeast.bytepluses.com/api/v3` → chat endpoint `.../chat/completions`. Use the `openai` SDK with this `base_url`.
- **Auth:** `Authorization: Bearer <ARK_API_KEY>` (the SDK adds it from `api_key`). Key in `.env` as `ARK_API_KEY` (gitignored) — load via dotenv, **never hardcode**.
- **Model ID (confirmed):** `seed-2-0-lite-260428` — put this exact lowercase string in the `model` field (NOT the display name `Dola-Seed-2.0-lite/260428`). Input: Text+Images+Video+Audio; Output: Text only.
- **Non-standard params** (`reasoning_effort`, `thinking`, `fps`) pass via `extra_body` with the OpenAI SDK.
- **APIs:** Response API (supports Files API upload + explicit cache) and Chat API.
- **Context:** 256K window, 224K max input. **Max output:** 128k (default 4k, excl. reasoning) — set `max_tokens` explicitly for long transcripts.
- **Rate limits:** RPM 30,000 · TPM 1.5M. Run independent calls concurrently.
- **Pricing (USD / 1M tokens):** ≤128k → input 0.25, **audio 3.75**, output 2.0 · 128–256k → 0.5 / 7.5 / 4.0. (Audio ≈ 15× text — minimize audio tokens.)

## Structured output — use FUNCTION CALLING (not JSON Schema)
`response_format` JSON Object / JSON Schema are **not GA yet** (and Batch is not GA). To force a schema: **define a tool with the target schema and require the model to call it**, then **validate** the arguments (Pydantic) and retry on mismatch. This is the structured-extraction path for `audio-understanding` and `visual-indexing`.

## Reasoning effort (the main cost/latency lever)
`reasoning_effort`: `minimal | low | medium (default) | high`. Thinking is **on by default**.
- **Indexing / extraction (Stages 2–3):** `low` or `minimal`.
- **Q&A / verification (Stage 6):** `medium` / `high`.
- Thinking-summary adds inter-token latency → raise request timeout. In multi-turn tool calls, pass back `encrypted_content` (preferred) or `reasoning_content` to avoid degraded reasoning; single-shot extraction needs neither.

## Input methods (video)
| Method | Size limit | Format |
|---|---|---|
| Files API → `file_id` | ≤512 MB | upload first; best for segments / large video |
| base64 | video ≤50 MB & request ≤64 MB | `data:video/mp4;base64,...` (mov: `video/mov`), **lowercase** |
| URL | ≤50 MB | file on TOS with correct Content-Type (mov: `video/quicktime`) |
- **Frames (images):** base64 inline is simplest for the few frames per window.
- **Video token budget:** ≤**80k tokens/video/request**. seed-2-0 frame tokens ∈ [64, 384]; frames ∈ [16, 1280]. → ~1280 low-res (64 tok) OR ~213 high-res (384 tok) frames per call. `fps` ∈ [0.2, 5] (default 1). Native video auto-marks `timestamp + image`.

## Cost / latency capture (feeds dashboard-ui)
Every call returns `usage`; record `{model, prompt/audio/image/output tokens, cost_usd, latency_ms, reasoning_effort, cache_hit}` into the window/answer `_meta`. Cost = tokens × tiered price. Enable **prefix/explicit cache** for the repeated extraction system prompt.

## Definition of done
A single `call_seed(...)` wrapper: picks input method, supports tool-forced structured output + validation/retry, sets reasoning_effort/image-quality/fps, enforces the 80k video budget, and emits `_meta` for every call.
