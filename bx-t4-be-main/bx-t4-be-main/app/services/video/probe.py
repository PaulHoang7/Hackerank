import json
import shutil
import subprocess
from pathlib import Path

from app.core.exceptions import AppError


def ensure_ffmpeg_available() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise AppError("FFMPEG_NOT_AVAILABLE", "FFmpeg and FFprobe must be installed")


def extract_metadata(path: Path) -> dict:
    ensure_ffmpeg_available()
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=codec_type,codec_name,width,height",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise AppError("VIDEO_METADATA_FAILED", "Unable to extract video metadata", details=result.stderr)
    data = json.loads(result.stdout)
    duration = float(data.get("format", {}).get("duration") or 0)
    return {"duration_seconds": duration, "raw": data}


def transcode_proxy(input_path: Path, output_path: Path, max_height: int = 720) -> None:
    """Transcode the source to a lightweight playback/analysis proxy.

    Downscales to at most ``max_height`` (never upscales), re-encodes H.264 + AAC
    with faststart so a multi-hundred-MB upload becomes a few tens of MB. The
    proxy is reused for every thumbnail/clip extraction below, so chunk work also
    gets faster.
    """
    ensure_ffmpeg_available()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vf",
            f"scale=-2:'min({max_height},ih)'",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if result.returncode != 0:
        raise AppError("PROXY_TRANSCODE_FAILED", "Unable to transcode proxy", details=result.stderr)


def extract_thumbnail(input_path: Path, output_path: Path, timestamp: float) -> None:
    ensure_ffmpeg_available()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(max(0.0, timestamp)),
            "-i",
            str(input_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise AppError("THUMBNAIL_FAILED", "Unable to extract thumbnail", details=result.stderr)


def extract_clip(input_path: Path, output_path: Path, start_time: float, end_time: float) -> None:
    ensure_ffmpeg_available()
    duration = max(0.1, end_time - start_time)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(max(0.0, start_time)),
            "-i",
            str(input_path),
            "-t",
            str(duration),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "28",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise AppError("CLIP_EXTRACT_FAILED", "Unable to extract video window clip", details=result.stderr)
