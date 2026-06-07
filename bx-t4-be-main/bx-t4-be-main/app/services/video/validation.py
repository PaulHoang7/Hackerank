import os

from fastapi import UploadFile

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm"}


async def validate_upload(file: UploadFile, settings: Settings | None = None) -> int:
    settings = settings or get_settings()
    content_type = file.content_type or ""
    if content_type not in settings.allowed_video_content_types:
        raise AppError("UNSUPPORTED_VIDEO_TYPE", "Only MP4, MOV and WebM videos are supported")
    suffix = "." + (file.filename or "").rsplit(".", 1)[-1].lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise AppError("UNSUPPORTED_VIDEO_EXTENSION", "Only .mp4, .mov and .webm files are supported")

    # Measure size by seeking the already-spooled upload instead of reading the
    # whole file into memory (a 600MB upload no longer allocates 600MB of RAM).
    fileobj = file.file
    fileobj.seek(0, os.SEEK_END)
    file_size = fileobj.tell()
    fileobj.seek(0)
    if file_size <= 0:
        raise AppError("EMPTY_UPLOAD", "Uploaded video is empty")
    if file_size > settings.max_upload_size_bytes:
        raise AppError("UPLOAD_TOO_LARGE", "Uploaded video exceeds configured size limit")
    return file_size
