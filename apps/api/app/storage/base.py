import abc
from dataclasses import dataclass
from typing import IO, Protocol


@dataclass
class StorageUploadResult:
    object_key: str
    bucket: str | None = None


class StorageAdapter(Protocol):
    async def upload_file(self, object_key: str, file_bytes: bytes, content_type: str) -> StorageUploadResult:
        raise NotImplementedError

    async def upload_stream(self, object_key: str, file_obj: IO[bytes], content_type: str) -> StorageUploadResult:
        raise NotImplementedError

    async def delete_file(self, object_key: str, bucket: str | None = None) -> None:
        raise NotImplementedError

    async def generate_presigned_url(self, object_key: str, bucket: str | None = None, expires_in: int = 3600) -> str:
        raise NotImplementedError
