import re
from pathlib import Path
from uuid import uuid4

_SAFE_FILENAME = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name.strip().replace(" ", "_")
    cleaned = _SAFE_FILENAME.sub("", name)
    return cleaned or f"upload-{uuid4()}.bin"


def build_storage_key(video_id: str, filename: str) -> str:
    return f"videos/{video_id}/{sanitize_filename(filename)}"
