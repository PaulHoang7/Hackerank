---
name: video-ingestion
description: Use when ingesting or preprocessing source video before indexing — accepting an upload/URL, storing the raw file, parsing the optional context kit, detecting scene boundaries, planning virtual time windows, and extracting frames/thumbnails + the audio track. Stages 0–1 of the pipeline. Read 00-overview first.
---

# video-ingestion · Stages 0–1 (Intake & Window Planning)

Deterministic, no AI. Turns a raw video into the structural skeleton the model passes operate on. **Windows are virtual timestamp ranges — never render clips for output.**

## When to use
A new video/URL arrives, or you need to (re)compute windows, thumbnails, or the audio track.

## Inputs → Outputs
- **In:** video file or URL (MP4/MOV/HLS); optional **context kit** (SKU list + product images, banned/required claims per market, target languages, host/creator names).
- **Out:** raw video in storage; an Index skeleton with `windows[]` populated structurally (no semantics yet); extracted thumbnails; an audio track file; pre-computed catalog image embeddings.

## Steps
1. **Intake (Stage 0)** — accept upload / pull URL → store raw video to **S3/TOS**. Create a **job record** and **enqueue async** (heavy work must not block the request). Init Index skeleton with `video` block, `status="queued"`.
2. **Parse context kit** — load SKU catalog; **compute catalog image embeddings now** (entity-sku-timeline needs them in Stage 4). Load compliance rules (banned/required claims).
3. **Scene detection** — **PySceneDetect** → shot boundaries → window list. Long scene with no cut → **cap at 8–15s** (sub-split); merge sub-min fragments.
4. **Window planning** — windows are **contiguous** (window N ends where N+1 begins, sharing the boundary frame → no gaps). Add ~1s overlap **only** at artificial sub-split boundaries (flag them so later stages dedupe).
5. **Frame/thumbnail extraction** — **ffmpeg**, 2–3 frames/window (start/mid + a frame where on-screen text changes). Use `-c copy`-style fast seeking; write thumbnails to storage, keep URLs. These are **evidence** assets.
6. **Audio extraction** — ffmpeg → single audio track file for `audio-understanding` (do NOT cut per-window audio here).

## Writes to Index
`windows[].window_id, start_time, end_time, thumbnails[]`, plus a `sub_split:true` flag on artificial boundaries. Aggregates nothing semantic.

## Gotchas / locked decisions
- **No fixed 5s grid.** Scene-aware windows cut on content change → better retrieval + far fewer model calls (cost).
- **±3s does not require tiny windows** — precision comes from intra-window timestamps produced later (ASR word timestamps, OCR frame timestamps).
- One mid-frame per window is not enough for OCR/compliance — extract 2–3, including text-change frames.
- HLS/live recordings: normalize to a seekable container first if needed.

## Definition of done
`status` advances to `ingested`; `windows[]` tiles the full duration with no gaps; thumbnails resolve; audio track exists; catalog embeddings cached.
