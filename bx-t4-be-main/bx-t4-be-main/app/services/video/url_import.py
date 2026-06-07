from __future__ import annotations

import mimetypes
import os
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from starlette import status

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.security import sanitize_filename


@dataclass(frozen=True)
class ImportedVideoFile:
    path: Path
    filename: str
    content_type: str
    file_size: int


def import_public_video_url(url: str, settings: Settings | None = None) -> ImportedVideoFile:
    settings = settings or get_settings()
    clean_url = validate_import_url(url, settings)

    work_dir = Path(tempfile.mkdtemp(prefix="bxt4-url-import-"))
    output_template = str(work_dir / "%(title).180B-%(id)s.%(ext)s")
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "--format",
        "bestvideo+bestaudio/best",
        "--merge-output-format",
        "mp4",
        "--max-filesize",
        str(settings.external_import_max_size_bytes),
        "--socket-timeout",
        str(max(5, settings.external_import_timeout_seconds)),
        "--retries",
        "2",
        "--fragment-retries",
        "2",
        "--output",
        output_template,
        clean_url,
    ]

    try:
        _run_ytdlp(command, work_dir, timeout=max(30, settings.external_import_timeout_seconds))
    except FileNotFoundError as exc:
        raise AppError(
            "URL_IMPORT_DEPENDENCY_MISSING",
            "yt-dlp is not installed for this backend environment",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise AppError(
            "URL_IMPORT_TIMEOUT",
            "External video import timed out. For live streams, record a short clip first.",
            status.HTTP_408_REQUEST_TIMEOUT,
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or exc.stdout or "").strip()
        raise AppError(
            "URL_IMPORT_FAILED",
            "Cannot import this public URL with yt-dlp",
            status.HTTP_400_BAD_REQUEST,
            details=stderr[-2000:] if stderr else None,
        ) from exc

    media_path = _find_downloaded_media(work_dir)
    file_size = media_path.stat().st_size
    if file_size <= 0:
        raise AppError("URL_IMPORT_EMPTY_FILE", "Imported media file is empty")
    if file_size > settings.external_import_max_size_bytes:
        raise AppError(
            "URL_IMPORT_TOO_LARGE",
            "Imported media exceeds max import size",
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    content_type = mimetypes.guess_type(media_path.name)[0] or "video/mp4"
    filename = sanitize_filename(media_path.name)
    return ImportedVideoFile(
        path=media_path,
        filename=filename,
        content_type=content_type,
        file_size=file_size,
    )


def validate_import_url(url: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    clean_url = (url or "").strip()
    parsed = urlparse(clean_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise AppError("URL_IMPORT_INVALID_URL", "A valid http(s) URL is required")

    host = parsed.hostname.lower() if parsed.hostname else ""
    allowed_hosts = {item.lower() for item in settings.external_import_allowed_hosts}
    if host not in allowed_hosts and not any(host.endswith(f".{item}") for item in allowed_hosts):
        raise AppError(
            "URL_IMPORT_HOST_NOT_ALLOWED",
            "Only configured public TikTok/Douyin hosts can be imported",
            status.HTTP_400_BAD_REQUEST,
            details={"host": host},
        )
    return clean_url


def _find_downloaded_media(work_dir: Path) -> Path:
    ignored_suffixes = {".part", ".ytdl", ".json", ".webp", ".jpg", ".jpeg", ".png", ".description"}
    candidates = [
        path
        for path in work_dir.iterdir()
        if path.is_file() and not any(path.name.endswith(suffix) for suffix in ignored_suffixes)
    ]
    if not candidates:
        raise AppError("URL_IMPORT_NO_MEDIA", "yt-dlp did not produce a media file")
    return max(candidates, key=lambda path: path.stat().st_size)


def _run_ytdlp(command: list[str], work_dir: Path, *, timeout: int) -> subprocess.CompletedProcess[str]:
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        cwd=str(work_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creationflags,
        start_new_session=os.name != "nt",
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_tree(process.pid)
        stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr) from exc

    completed = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    if completed.returncode:
        raise subprocess.CalledProcessError(completed.returncode, command, output=stdout, stderr=stderr)
    return completed


def _terminate_process_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, text=True)
        return
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
