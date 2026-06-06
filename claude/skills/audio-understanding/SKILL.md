---
name: audio-understanding
description: Use when transcribing and understanding the audio track — chunked ASR + speech translation (AST) producing multilingual timestamped transcript, the canonical text_en layer, speaker diarization, audio events, and the energy curve. Stage 2 of the pipeline. Calls the model via seed-omni-reasoning. Read 00-overview first.
---

# audio-understanding · Stage 2 (Audio Pass)

Understand the whole audio track **once**, multilingual, with timestamps. **Invariant: each second of audio is sent to the model exactly once** — this preserves the audio-cost win (audio ≈ 15× text).

## When to use
After ingestion, to produce the transcript/audio layer of the index, or to (re)transcribe.

## Inputs → Outputs
- **In:** the extracted audio track; the window list (for timestamp assignment).
- **Out:** a continuous timestamped multilingual transcript with `text_en`, speaker labels, audio events, and `energy`, sliced onto each window.

## Steps (Audio Chunking Pass)
1. **Chunk into ~5–10 min blocks** cut on **silence (VAD)** / scene boundaries — never mid-word. Blocks do **not** overlap (or ≤1–2s safety overlap at the seam, then dedupe seam text).
2. **Per block, one ASR+AST call** (`reasoning_effort: low`, `max_tokens` large enough for the transcript):
   - **ASR + subtitle-aligned timestamps** → `transcript_original` + word/segment `word_timestamps` (the ±3s source).
   - **AST → English** → `transcript_en` (canonical layer for cross-language search & entity linking). SEA support: vi/th/id ↔ en.
   - **Speaker diarization** → `speaker` (separate host vs guests/chat).
   - **Audio events** (purchase jingle, laughter, high-energy voice) → `audio_events`; derive **`energy` 0..1** for the energy curve.
3. **Run blocks concurrently** (RPM/TPM allow it) → wall-clock ≈ one block.
4. **Stitch** by adding each block's start offset to all in-block timestamps → one continuous transcript.
5. **Slice to windows** by timestamp → fill each window's audio fields.

## Writes to Index
`transcript_original, transcript_en, lang_spans, speaker, word_timestamps, audio_events, energy` on each window.

## Gotchas / locked decisions
- A single giant call would exceed 224K input — **chunking is mandatory** and the same code path serves 5 min → 4 h (just more blocks).
- Reserve context headroom for transcript output + reasoning; if output nears `max_tokens`, shrink the block.
- Tag code-switching in `lang_spans`; do downstream linking on `text_en` + visual, never on raw mixed strings.
- Do not re-send audio per window (kills the cost win).

## Definition of done
Continuous transcript with correct global timestamps; `text_en` present for non-English speech; every window has its audio fields; audio billed ≈ 1× duration.
