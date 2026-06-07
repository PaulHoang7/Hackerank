"""Phase 3: dedicated ASR pipeline.

Extracts audio from proxy video, splits into ~30s blocks at VAD silence points,
transcribes each block via Seed multilingual ASR, and enriches VideoWindow records
in-place with accurate transcript, translation, audio_events, and energy_score.

This runs AFTER the visual analysis so it only overwrites fields that benefit from
a dedicated audio pass (transcript, translation, audio_events, energy_score).
Visual-only fields (scene_description, ocr_text, detected_entities) are preserved.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
import subprocess
import tempfile
from pathlib import Path

import httpx
import numpy as np
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import VideoWindow

logger = logging.getLogger(__name__)

BLOCK_SEC = 30.0
BLOCK_MIN = BLOCK_SEC * 0.5
BLOCK_MAX = BLOCK_SEC * 1.6
SILENCE_DB = -30
SILENCE_MIN = 0.25
SR = 16000

ASR_SYSTEM = (
    "You are an expert multilingual speech analyst for Southeast-Asian e-commerce "
    "livestreams (TikTok Shop / Shopee Live), where the host speaks Vietnamese/Thai "
    "with English code-switching for product and brand names.\n"
    "Transcribe the audio into SHORT, sentence-level segments covering the ENTIRE clip. "
    "For each segment provide:\n"
    "  - start, end: seconds RELATIVE to the start of THIS audio clip (be accurate)\n"
    "  - speaker: 'host', 'guest', or 'unknown'\n"
    "  - lang: primary ISO code of the segment ('vi','th','id','en',...)\n"
    "  - text_original: verbatim transcript, preserving code-switching\n"
    "  - text_en: faithful English translation (copy if already English)\n"
    "  - audio_events: any of [high_energy_voice, laughter, music, jingle, applause, silence, crosstalk]\n"
    "Do NOT invent speech that is not there.\n"
    "Return JSON array of segments only (no markdown fences):\n"
    '[{"start":0,"end":3,"speaker":"host","lang":"vi","text_original":"...","text_en":"...","audio_events":[]}]'
)


class ASRSegment(BaseModel):
    start: float = 0.0
    end: float = 0.0
    speaker: str = "host"
    lang: str = "vi"
    text_original: str = ""
    text_en: str = ""
    audio_events: list[str] = Field(default_factory=list)


def _ffprobe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        stdout=subprocess.PIPE, text=True, check=False,
    ).stdout.strip()
    return float(out) if out else 0.0


def _detect_silences(audio: Path) -> list[float]:
    """Return midpoints of silence regions — good VAD cut points."""
    out = subprocess.run(
        ["ffmpeg", "-i", str(audio), "-af",
         f"silencedetect=noise={SILENCE_DB}dB:d={SILENCE_MIN}", "-f", "null", "-"],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=False,
    ).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    mids = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else s + SILENCE_MIN
        mids.append(round((s + e) / 2, 2))
    return sorted(mids)


def plan_blocks(duration: float, silences: list[float] | None = None) -> list[tuple[float, float]]:
    if duration <= BLOCK_SEC:
        return [(0.0, round(duration, 2))]
    if not silences:
        blocks, t = [], 0.0
        while t < duration:
            blocks.append((t, round(min(t + BLOCK_SEC, duration), 2)))
            t += BLOCK_SEC
        return blocks
    blocks, start = [], 0.0
    while start < duration:
        if start + BLOCK_MAX >= duration:
            blocks.append((start, round(duration, 2)))
            break
        ideal, lo, hi = start + BLOCK_SEC, start + BLOCK_MIN, start + BLOCK_MAX
        cands = [s for s in silences if lo <= s <= hi]
        cut = min(cands, key=lambda s: abs(s - ideal)) if cands else round(ideal, 2)
        blocks.append((start, cut))
        start = cut
    return blocks


def _extract_audio(video: Path, output: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video),
         "-vn", "-ac", "1", "-ar", str(SR), "-b:a", "64k", str(output)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )


def _slice_audio(audio: Path, start: float, end: float) -> Path:
    tmp = Path(tempfile.mkdtemp()) / f"blk_{int(start)}.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{start:.2f}", "-to", f"{end:.2f}",
         "-i", str(audio), "-ac", "1", "-ar", str(SR), "-b:a", "64k", str(tmp)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )
    return tmp


def _audio_data_url(path: Path) -> str:
    mime = "audio/mpeg"
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{data}"


def _compute_energy(audio: Path, windows: list[VideoWindow]) -> None:
    """Per-window RMS energy score, normalized to 0..1."""
    try:
        raw = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(audio),
             "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        ).stdout
        samples = np.frombuffer(raw, dtype=np.float32)
    except Exception:
        return
    if samples.size == 0:
        return
    rms = []
    for w in windows:
        seg = samples[int(w.start_time * SR): int(w.end_time * SR)]
        rms.append(float(np.sqrt(np.mean(seg ** 2))) if seg.size else 0.0)
    arr = np.array(rms)
    norm = float(np.percentile(arr, 95)) or 1.0
    for w, v in zip(windows, arr):
        w.energy_score = round(float(min(v / norm, 1.0)), 3)


async def _transcribe_block(
    api_key: str, base_url: str, model: str, timeout: float,
    audio_path: Path, block_start: float, block_end: float, single: bool,
) -> list[ASRSegment]:
    """One Seed API call to transcribe a single audio block."""
    clip = audio_path if single else await asyncio.to_thread(_slice_audio, audio_path, block_start, block_end)
    data_url = await asyncio.to_thread(_audio_data_url, clip)
    duration = round(block_end - block_start, 1)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": ASR_SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Audio clip duration ≈ {duration}s. Transcribe fully."},
                    {"type": "audio_url", "audio_url": {"url": data_url}},
                ],
            },
        ],
        "max_tokens": 8192,
    }

    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(timeout, read=timeout),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    ) as client:
        resp = await client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]

    # strip markdown fences if present
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    # find JSON array
    m2 = re.search(r"\[.*\]", text, re.DOTALL)
    raw_list = json.loads(m2.group(0) if m2 else text)

    segments = []
    for item in raw_list if isinstance(raw_list, list) else []:
        try:
            seg = ASRSegment(**{k: v for k, v in item.items() if k in ASRSegment.model_fields})
            # stitch: add block offset
            seg.start = round(seg.start + block_start, 2)
            seg.end = round(seg.end + block_start, 2)
            segments.append(seg)
        except Exception:
            continue
    if not single and clip != audio_path:
        try:
            clip.unlink(missing_ok=True)
            clip.parent.rmdir()
        except Exception:
            pass
    return segments


def _assign_segments(windows: list[VideoWindow], segments: list[ASRSegment]) -> None:
    """Assign each ASR segment to the window it overlaps most."""
    for w in windows:
        w.transcript = ""
        w.translation = ""

    for s in segments:
        best, best_ov = None, 0.0
        for w in windows:
            ov = min(s.end, w.end_time) - max(s.start, w.start_time)
            if ov > best_ov:
                best_ov, best = ov, w
        if best is None:
            continue
        best.transcript = (best.transcript + " " + s.text_original).strip()
        best.translation = (best.translation + " " + s.text_en).strip()
        # Merge audio_events — keep unique values, dicts or strings
        existing_events = {
            e.get("event", e) if isinstance(e, dict) else e
            for e in (best.audio_events or [])
        }
        for ev in s.audio_events:
            if ev not in existing_events:
                best.audio_events = list(best.audio_events or []) + [{"event": ev, "source": "asr"}]
                existing_events.add(ev)


async def run_asr(
    session: AsyncSession,
    video_id: str,
    local_video: Path,
) -> int:
    """Run ASR on `local_video`, enrich VideoWindow rows in DB.
    Returns number of windows updated.
    """
    settings = get_settings()
    if not settings.seed_omni_api_key:
        logger.warning("asr_skipped_no_api_key video_id=%s", video_id)
        return 0

    result = await session.scalars(
        select(VideoWindow).where(VideoWindow.video_id == video_id).order_by(VideoWindow.start_time)
    )
    windows = list(result.all())
    if not windows:
        return 0

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / "audio.mp3"
        try:
            await asyncio.to_thread(_extract_audio, local_video, audio_path)
        except Exception:
            logger.exception("asr_audio_extract_failed video_id=%s", video_id)
            return 0

        duration = await asyncio.to_thread(_ffprobe_duration, audio_path)
        silences = await asyncio.to_thread(_detect_silences, audio_path)
        blocks = plan_blocks(duration, silences)
        single = len(blocks) == 1

        logger.info("asr_blocks video_id=%s duration=%.1f blocks=%d", video_id, duration, len(blocks))

        concurrency = max(1, settings.seed_analysis_concurrency)
        sem = asyncio.Semaphore(concurrency)

        async def _bounded(bstart: float, bend: float) -> list[ASRSegment]:
            async with sem:
                try:
                    return await _transcribe_block(
                        settings.seed_omni_api_key,
                        settings.seed_omni_base_url.rstrip("/"),
                        settings.seed_omni_model,
                        settings.external_api_timeout_seconds,
                        audio_path, bstart, bend, single,
                    )
                except Exception:
                    logger.exception("asr_block_failed video_id=%s start=%.1f", video_id, bstart)
                    return []

        tasks = [asyncio.create_task(_bounded(s, e)) for s, e in blocks]
        all_segs: list[ASRSegment] = []
        for fut in asyncio.as_completed(tasks):
            segs = await fut
            all_segs.extend(segs)
        all_segs.sort(key=lambda s: s.start)

        _assign_segments(windows, all_segs)
        _compute_energy(audio_path, windows)

    for w in windows:
        session.add(w)
    await session.commit()

    logger.info(
        "asr_completed video_id=%s windows=%d segments=%d",
        video_id, len(windows), len(all_segs),
    )
    return len(windows)
