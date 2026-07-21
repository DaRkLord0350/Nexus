import asyncio
import shutil
from pathlib import Path
from typing import IO

from app.core.config import settings
from app.storage.base import StorageAdapter, StorageUploadResult


class LocalStorageAdapter(StorageAdapter):
    def __init__(self, base_path: Path | None = None):
        self.base_path = (base_path or settings.local_upload_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(self, object_key: str, file_bytes: bytes, content_type: str) -> StorageUploadResult:
        path = self.base_path / object_key
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, file_bytes)
        return StorageUploadResult(object_key=object_key)

    async def upload_stream(self, object_key: str, file_obj: IO[bytes], content_type: str) -> StorageUploadResult:
        path = self.base_path / object_key
        path.parent.mkdir(parents=True, exist_ok=True)

        def _copy() -> None:
            with open(path, "wb") as destination:
                shutil.copyfileobj(file_obj, destination)

        await asyncio.to_thread(_copy)
        return StorageUploadResult(object_key=object_key)

    async def delete_file(self, object_key: str, bucket: str | None = None) -> None:
        path = self.base_path / object_key
        if path.exists():
            await asyncio.to_thread(path.unlink)

    async def generate_presigned_url(self, object_key: str, bucket: str | None = None, expires_in: int = 3600) -> str:
        raise NotImplementedError("Local storage does not support direct presigned URLs. Use backend download endpoints instead.")
