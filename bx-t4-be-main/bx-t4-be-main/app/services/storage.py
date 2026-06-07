import shutil
from pathlib import Path
from typing import BinaryIO, Protocol

from app.core.config import get_settings


class StorageService(Protocol):
    def upload_fileobj(self, storage_key: str, fileobj: BinaryIO, file_size: int, content_type: str) -> None:
        ...

    def upload_path(self, storage_key: str, source_path: Path, content_type: str) -> None:
        ...

    def download_to_path(self, storage_key: str, destination_path: Path) -> None:
        ...

    def get_file_url(self, storage_key: str) -> str:
        ...

    def delete_file(self, storage_key: str) -> None:
        ...


class LocalStorageService:
    def __init__(self, root_path: str, public_url: str) -> None:
        self.root_path = Path(root_path)
        self.public_url = public_url.rstrip("/")

    def upload_fileobj(self, storage_key: str, fileobj: BinaryIO, file_size: int, content_type: str) -> None:
        destination = self._path_for_key(storage_key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as output:
            shutil.copyfileobj(fileobj, output)

    def upload_path(self, storage_key: str, source_path: Path, content_type: str) -> None:
        destination = self._path_for_key(storage_key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)

    def download_to_path(self, storage_key: str, destination_path: Path) -> None:
        source = self._path_for_key(storage_key)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination_path)

    def get_file_url(self, storage_key: str) -> str:
        return f"{self.public_url}/{self._clean_key(storage_key)}"

    def delete_file(self, storage_key: str) -> None:
        path = self._path_for_key(storage_key)
        if path.exists():
            path.unlink()

    def _path_for_key(self, storage_key: str) -> Path:
        return self.root_path / self._clean_key(storage_key)

    @staticmethod
    def _clean_key(storage_key: str) -> str:
        return storage_key.strip().lstrip("/")


def get_storage_service() -> StorageService:
    settings = get_settings()
    if settings.storage_provider != "local":
        raise ValueError(f"Unsupported storage provider: {settings.storage_provider}")
    return LocalStorageService(
        root_path=settings.local_storage_path,
        public_url=settings.storage_public_url,
    )
