import asyncio
from typing import IO

from app.core.config import settings
from app.storage.base import StorageAdapter, StorageUploadResult

# Explicit multipart tuning rather than relying on boto3's implicit defaults:
# anything above 8MB is uploaded in 8MB parts, concurrently. This is what
# makes "large file support" real rather than accidental.
_MULTIPART_THRESHOLD_BYTES = 8 * 1024 * 1024
_MULTIPART_CHUNKSIZE_BYTES = 8 * 1024 * 1024
_MAX_CONCURRENCY = 4


class S3StorageAdapter(StorageAdapter):
    def __init__(self, endpoint_url: str | None = None):
        try:
            import boto3
            from boto3.s3.transfer import TransferConfig
        except ImportError as exc:
            raise RuntimeError("boto3 is required for the S3 storage adapter") from exc

        self.endpoint_url = endpoint_url or settings.s3_endpoint or None
        self.bucket = settings.s3_bucket
        self.transfer_config = TransferConfig(
            multipart_threshold=_MULTIPART_THRESHOLD_BYTES,
            multipart_chunksize=_MULTIPART_CHUNKSIZE_BYTES,
            max_concurrency=_MAX_CONCURRENCY,
            use_threads=True,
        )
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=settings.s3_region,
            **settings.aws_credentials_kwargs,
        )

    async def upload_file(self, object_key: str, file_bytes: bytes, content_type: str) -> StorageUploadResult:
        await asyncio.to_thread(
            self.client.put_object,
            Bucket=self.bucket,
            Key=object_key,
            Body=file_bytes,
            ContentType=content_type,
        )
        return StorageUploadResult(object_key=object_key, bucket=self.bucket)

    async def upload_stream(self, object_key: str, file_obj: IO[bytes], content_type: str) -> StorageUploadResult:
        await asyncio.to_thread(
            self.client.upload_fileobj,
            file_obj,
            self.bucket,
            object_key,
            ExtraArgs={"ContentType": content_type},
            Config=self.transfer_config,
        )
        return StorageUploadResult(object_key=object_key, bucket=self.bucket)

    async def delete_file(self, object_key: str, bucket: str | None = None) -> None:
        await asyncio.to_thread(
            self.client.delete_object,
            Bucket=bucket or self.bucket,
            Key=object_key,
        )

    async def generate_presigned_url(self, object_key: str, bucket: str | None = None, expires_in: int = 3600) -> str:
        return await asyncio.to_thread(
            self.client.generate_presigned_url,
            ClientMethod="get_object",
            Params={"Bucket": bucket or self.bucket, "Key": object_key},
            ExpiresIn=expires_in,
        )
