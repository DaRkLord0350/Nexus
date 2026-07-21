from app.core.config import settings
from app.storage.local_storage import LocalStorageAdapter
from app.storage.s3_storage import S3StorageAdapter


def build_storage_adapter() -> LocalStorageAdapter | S3StorageAdapter:
    provider = settings.storage_provider.lower()
    if provider == "local":
        return LocalStorageAdapter()

    if provider == "s3":
        return S3StorageAdapter()

    raise ValueError(f"Unsupported storage provider: {settings.storage_provider}. Expected 'local' or 's3'.")
